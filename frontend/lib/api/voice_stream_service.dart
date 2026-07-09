import 'dart:async';
import 'dart:typed_data';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';

import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/Dio.dart';

/// 语音流式输入服务
///
/// 负责以下功能：
/// 1. 麦克风权限管理
/// 2. 音频录制
/// 3. 将音频流实时发送到后端进行 ASR 识别
/// 4. 接收后端返回的识别结果
class VoiceStreamService {
  final AudioRecorder _audioRecorder = AudioRecorder();
  
  // 当前会话 ID
  String? _sessionId;
  
  // 录音状态
  bool _isRecording = false;
  
  // 识别文本流控制器
  final StreamController<String> _textStreamController = StreamController<String>.broadcast();
  
  // 任务结果流控制器（用于传递最终的 task 结构化数据）
  final StreamController<Map<String, dynamic>> _taskStreamController = StreamController<Map<String, dynamic>>.broadcast();
  
  // 错误流控制器
  final StreamController<String> _errorStreamController = StreamController<String>.broadcast();
  
  // DioUtils 实例
  final DioUtils _dioUtils = DioUtils();

  /// 识别文本流
  Stream<String> get textStream => _textStreamController.stream;
  
  /// 任务结果流
  Stream<Map<String, dynamic>> get taskStream => _taskStreamController.stream;
  
  /// 错误流
  Stream<String> get errorStream => _errorStreamController.stream;
  
  /// 当前是否正在录音
  bool get isRecording => _isRecording;

  /// 请求麦克风权限
  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }
  
  /// 检查麦克风权限状态
  Future<bool> hasPermission() async {
    final status = await Permission.microphone.status;
    return status.isGranted;
  }
  
  /// 生成唯一的会话 ID
  String _generateSessionId() {
    return DateTime.now().millisecondsSinceEpoch.toString();
  }
  
  /// 开始语音识别会话
  /// 
  /// 流程：
  /// 1. 检查麦克风权限
  /// 2. 生成会话 ID
  /// 3. 调用后端 /api/voice/start 接口初始化会话
  /// 4. 开始录音并实时发送音频数据
  Future<void> startListening() async {
    if (_isRecording) return;
    
    // 检查权限
    if (!await hasPermission()) {
      final granted = await requestPermission();
      if (!granted) {
        _errorStreamController.add("Microphone permission not granted");
        throw Exception('Microphone permission not granted');
      }
    }
    
    // 生成会话 ID
    _sessionId = _generateSessionId();
    
    try {
      // 调用后端开始会话
      await _dioUtils.post(HttpConstants.VOICE_START, data: {
        'session_id': _sessionId
      });
    } catch (e) {
      _errorStreamController.add("Failed to start voice session: $e");
      throw Exception('Failed to start voice session: $e');
    }
    
    // 开始录音
    _isRecording = true;
    
    try {
      // 配置录音参数：16kHz 采样率，单声道，16bit PCM
      final audioStream = await _audioRecorder.startStream(
        const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 16000,
          numChannels: 1,
        ),
      );
      
      // 监听录音数据流
      audioStream.listen(
        (data) => _sendAudioChunk(data),
        onError: (error) {
          _errorStreamController.add("Audio stream error: $error");
        },
        onDone: () {
          // 录音停止时的处理
        },
      );
    } catch (e) {
      _isRecording = false;
      _errorStreamController.add("Failed to start recording: $e");
      throw Exception('Failed to start recording: $e');
    }
  }
  
  /// 发送音频数据块到后端
  /// 
  /// 将录制的 PCM 音频数据实时发送到后端进行 ASR 识别
  Future<void> _sendAudioChunk(Uint8List data) async {
    if (!_isRecording || _sessionId == null) return;
    
    try {
      // 发送音频数据到后端
      final response = await _dioUtils.postBinary(
        HttpConstants.VOICE_AUDIO,
        data: data,
        queryParameters: {'session_id': _sessionId},
      );
      
      // 如果后端返回了识别文本，添加到结果流
      if (response.data != null && response.data['text'] != null) {
        final text = response.data['text'] as String;
        if (text.isNotEmpty) {
          _textStreamController.add(text);
        }
      }
    } catch (e) {
      // 忽略发送错误，避免影响录音过程
      print('Error sending audio chunk: $e');
    }
  }
  
  /// 停止语音识别
  /// 
  /// 流程：
  /// 1. 停止录音
  /// 2. 调用后端 /api/voice/stop 接口
  /// 3. 后端完成 ASR 识别并调用 LLM 进行任务提取
  /// 4. 返回最终识别文本和结构化任务数据
  Future<Map<String, dynamic>> stopListening() async {
    if (!_isRecording || _sessionId == null) {
      return {};
    }
    
    _isRecording = false;
    
    try {
      await _audioRecorder.stop();
    } catch (e) {
      print('Error stopping recorder: $e');
    }
    
    try {
      // 调用后端停止会话，获取最终结果
      final response = await _dioUtils.post(HttpConstants.VOICE_STOP, data: {
        'session_id': _sessionId
      });
      
      final result = response.data as Map<String, dynamic>;
      
      // 如果有任务数据，添加到任务流
      if (result['tasks'] != null) {
        final tasks = result['tasks'];
        if (tasks is List && tasks.isNotEmpty) {
          for (var task in tasks) {
            _taskStreamController.add(task as Map<String, dynamic>);
          }
        }
      }
      
      // 如果有错误，添加到错误流
      if (result['error'] != null) {
        _errorStreamController.add(result['error'] as String);
      }
      
      _sessionId = null;
      return result;
    } catch (e) {
      _errorStreamController.add("Failed to stop voice session: $e");
      throw Exception('Failed to stop voice session: $e');
    }
  }
  
  /// 取消语音识别会话
  /// 
  /// 与 stopListening 的区别：
  /// - cancel 不会进行 LLM 处理
  /// - 只会清理后端会话资源
  Future<void> cancelListening() async {
    if (!_isRecording || _sessionId == null) return;
    
    _isRecording = false;
    
    try {
      await _audioRecorder.stop();
    } catch (e) {
      print('Error stopping recorder: $e');
    }
    
    try {
      await _dioUtils.post(HttpConstants.VOICE_CANCEL, data: {
        'session_id': _sessionId
      });
    } catch (e) {
      print('Error cancelling voice session: $e');
    }
    
    _sessionId = null;
  }
  
  /// 释放资源
  Future<void> dispose() async {
    if (_isRecording) {
      await cancelListening();
    }
    await _audioRecorder.dispose();
    await _textStreamController.close();
    await _taskStreamController.close();
    await _errorStreamController.close();
  }
}
