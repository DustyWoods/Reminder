import 'dart:async';

import 'package:flutter/material.dart';
import 'package:reminder/api/sherpa_service.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class VoiceInput extends StatefulWidget {
  final Function(String)? onSet;
  final Function()? onClean;
  final Function()? onVoiceInputBegin;
  final Function()? onVoiceInputEnd;
  
  const VoiceInput({
    super.key, 
    required this.onSet, 
    required this.onClean, 
    required this.onVoiceInputBegin, 
    required this.onVoiceInputEnd,
  });

  @override
  State<VoiceInput> createState() => _VoiceInputState();
}

class _VoiceInputState extends State<VoiceInput> {
  final SherpaService _sherpaService = SherpaService();
  StreamSubscription<String>? _subscription;

  @override
  void dispose() {
    _subscription?.cancel();
    _sherpaService.dispose();
    super.dispose();
  }

  Future<void> _startListening() async {
    widget.onVoiceInputBegin?.call();
    widget.onClean?.call();
    
    await _sherpaService.startListening();
    
    _subscription = _sherpaService.textStream.listen(
      (text) {
        widget.onSet?.call(text);
      },
      onError: (error) {
        print("Sherpa 识别错误: $error");
      },
    );
  }

  void _stopListening() {
    widget.onVoiceInputEnd?.call();
    _subscription?.cancel();
    _subscription = null;
    _sherpaService.stopListening();
  }

  @override
  Widget build(BuildContext context) {
    return Positioned(
      bottom: 20,
      height: 60,
      width: ScreenSize.getWidth(context) * 0.8,
      right: ScreenSize.getWidth(context) * 0.1,
      child: Container(
        color: Colors.transparent,
        alignment: Alignment.center,
        child: GestureDetector(
          onLongPressStart: (_) => _startListening(),
          onLongPressEnd: (_) => _stopListening(),
          child: Container(
            width: ScreenSize.getWidth(context) * 0.8,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: const Color.fromARGB(255, 47, 98, 209),
              borderRadius: BorderRadius.circular(30),
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withValues(alpha: 0.2),
                  blurRadius: 20,
                  offset: const Offset(0, 4),
                ),
              ],
              border: Border.all(
                color: Colors.grey.withValues(alpha: 0.2),
                width: 1,
              ),
            ),
            child: const Icon(
              Icons.mic,
              size: 36,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}