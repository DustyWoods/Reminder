import 'dart:async';
import 'dart:typed_data';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:sherpa_onnx/sherpa_onnx.dart' as sherpa_onnx;

import 'package:reminder/Utils/audio_utils.dart';

class SherpaService {
  final AudioRecorder _audioRecorder = AudioRecorder();
  final StreamController<String> _textStreamController = StreamController<String>.broadcast();

  sherpa_onnx.OnlineRecognizer? _recognizer;
  sherpa_onnx.OnlineStream? _stream;

  bool _isListening = false;
  String _lastResult = '';
  bool _isInitialized = false;
  sherpa_onnx.OfflinePunctuation? _punctuation;

  Stream<String> get textStream => _textStreamController.stream;

  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  Future<bool> hasPermission() async {
    final status = await Permission.microphone.status;
    return status.isGranted;
  }

  Future<String> _getLocalModelPath(String assetPath) async {
    final dir = await getApplicationDocumentsDirectory();
    final fileName = assetPath.split('/').last;
    final localFile = File('${dir.path}/$fileName');

    if (!await localFile.exists()) {
      final bytes = await rootBundle.load(assetPath);
      await localFile.writeAsBytes(bytes.buffer.asUint8List());
    }

    return localFile.path;
  }

  Future<void> _initializeModels() async {
    if (_recognizer != null) return;

    try {
      if (!_isInitialized) {
        sherpa_onnx.initBindings();
        _isInitialized = true;
      }

      final encoderPath = await _getLocalModelPath('assets/models/zipformer/encoder-epoch-99-avg-1.onnx');
      final decoderPath = await _getLocalModelPath('assets/models/zipformer/decoder-epoch-99-avg-1.onnx');
      final joinerPath = await _getLocalModelPath('assets/models/zipformer/joiner-epoch-99-avg-1.onnx');
      final tokensPath = await _getLocalModelPath('assets/models/zipformer/tokens.txt');

      final modelConfig = sherpa_onnx.OnlineModelConfig(
        transducer: sherpa_onnx.OnlineTransducerModelConfig(
          encoder: encoderPath,
          decoder: decoderPath,
          joiner: joinerPath,
        ),
        tokens: tokensPath,
        numThreads: 4,
        provider: 'cpu',
      );

      final config = sherpa_onnx.OnlineRecognizerConfig(
        model: modelConfig,
        feat: sherpa_onnx.FeatureConfig(
          sampleRate: 16000,
        ),
        decodingMethod: 'greedy_search',
        maxActivePaths: 1,
      );

      _recognizer = sherpa_onnx.OnlineRecognizer(config);
      await _initializePunctuation();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> _initializePunctuation() async {
    if (_punctuation != null) return;

    try {
      final punctModelPath = await _getLocalModelPath('assets/models/punct/model.onnx');

      final punctModelConfig = sherpa_onnx.OfflinePunctuationModelConfig(
        ctTransformer: punctModelPath,
        numThreads: 4,
        provider: 'cpu',
        debug: false,
      );

      final punctConfig = sherpa_onnx.OfflinePunctuationConfig(
        model: punctModelConfig,
      );

      _punctuation = sherpa_onnx.OfflinePunctuation(config: punctConfig);
      print('SherpaService: Punctuation model initialized successfully');
    } catch (e) {
      print('SherpaService: Failed to initialize punctuation model: $e');
      print('SherpaService: Continuing without punctuation support');
    }
  }

  String _addPunctuation(String text) {
    if (_punctuation == null || text.isEmpty) {
      return text;
    }

    try {
      return _punctuation!.addPunct(text);
    } catch (e) {
      print('SherpaService: Error adding punctuation: $e');
      return text;
    }
  }

  Future<void> startListening() async {
    if (_isListening) return;

    if (!await hasPermission()) {
      final granted = await requestPermission();
      if (!granted) {
        throw Exception('Microphone permission not granted');
      }
    }

    await _initializeModels();

    _isListening = true;
    _lastResult = '';

    _stream = _recognizer?.createStream();
    if (_stream == null) {
      _isListening = false;
      throw Exception('Failed to create recognition stream');
    }

    try {
      if (await _audioRecorder.isRecording()) {
        await _audioRecorder.stop();
      }

      final audioStream = await _audioRecorder.startStream(
        const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 16000,
          numChannels: 1,
        ),
      );

      audioStream.listen(
        (data) {
          if (!_isListening || _stream == null || _recognizer == null) {
            return;
          }

          final samplesFloat32 = convertBytesToFloat32(Uint8List.fromList(data));

          _stream!.acceptWaveform(samples: samplesFloat32, sampleRate: 16000);
          while (_recognizer!.isReady(_stream!)) {
            _recognizer!.decode(_stream!);
          }

          final text = _recognizer!.getResult(_stream!).text;

          if (text.isNotEmpty && text != _lastResult) {
            _lastResult = text;
            final textWithPunctuation = _addPunctuation(text);
            _textStreamController.add(textWithPunctuation);
          }
        },
        onError: (error) {
          print('SherpaService: Stream error: $error');
        },
        onDone: () {
          print('SherpaService: Stream stopped.');
        },
      );
    } catch (e) {
      _isListening = false;
      rethrow;
    }
  }

  Future<void> stopListening() async {
    _isListening = false;

    try {
      await _audioRecorder.stop();
    } catch (e) {
      print('SherpaService: Error stopping recorder: $e');
    }

    if (_stream != null && _recognizer != null) {
      try {
        _stream!.inputFinished();

        while (_recognizer!.isReady(_stream!)) {
          _recognizer!.decode(_stream!);
        }

        final finalResult = _recognizer!.getResult(_stream!);
        if (finalResult.text.isNotEmpty && finalResult.text != _lastResult) {
          _lastResult = finalResult.text;
          final textWithPunctuation = _addPunctuation(finalResult.text);
          _textStreamController.add(textWithPunctuation);
        }

        _recognizer!.reset(_stream!);
        _stream!.free();
      } catch (e) {
        print('SherpaService: Error getting final result: $e');
      }

      _stream = null;
    }
  }

  Future<void> dispose() async {
    await stopListening();
    _textStreamController.close();
    _recognizer?.free();
    _punctuation?.free();
    _audioRecorder.dispose();
  }
}