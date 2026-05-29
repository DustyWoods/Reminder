import 'dart:async';

import 'package:flutter/material.dart';
import 'package:reminder/api/voice_stream_service.dart';
import 'package:reminder/Utils/ScreenSize.dart';

/// 语音输入按钮组件
///
/// 功能：
/// - 长按开始语音输入
/// - 松开结束语音输入
/// - 通过 VoiceStreamService 与后端通信进行实时 ASR 识别
class VoiceInput extends StatefulWidget {
  
  /// 语音输入开始时的回调
  final Function()? onVoiceInputBegin;
  
  /// 语音输入结束时的回调，携带最终结果
  final Function(Map<String, dynamic>)? onVoiceInputEnd;
  
  const VoiceInput({
    super.key, 
    required this.onVoiceInputBegin, 
    required this.onVoiceInputEnd,
  });

  @override
  State<VoiceInput> createState() => _VoiceInputState();
}

class _VoiceInputState extends State<VoiceInput> {
  // 流式语音服务实例
  final VoiceStreamService _voiceService = VoiceStreamService();
  
  // 订阅取消标记
  StreamSubscription<String>? _textSubscription;
  StreamSubscription<Map<String, dynamic>>? _taskSubscription;
  StreamSubscription<String>? _errorSubscription;

  @override
  void initState() {
    super.initState();
    // 监听识别文本变化
    _textSubscription = _voiceService.textStream.listen(
      (text) {
      },
      onError: (error) {
        print("Voice recognition error: $error");
      },
    );
    
    // 监听任务结果
    _taskSubscription = _voiceService.taskStream.listen(
      (task) {
        // 任务结果由 onVoiceInputEnd 统一处理
      },
    );
    
    // 监听错误
    _errorSubscription = _voiceService.errorStream.listen(
      (error) {
        print("Voice service error: $error");
      },
    );
  }

  @override
  void dispose() {
    _textSubscription?.cancel();
    _taskSubscription?.cancel();
    _errorSubscription?.cancel();
    _voiceService.dispose();
    super.dispose();
  }

  /// 开始语音输入
  /// 
  /// 用户长按按钮时调用：
  /// 1. 通知上层开始录音
  /// 2. 清除之前的识别文本
  /// 3. 启动流式语音服务
  Future<void> _startListening() async {
    widget.onVoiceInputBegin?.call();
    
    try {
      await _voiceService.startListening();
    } catch (e) {
      print("Failed to start listening: $e");
    }
  }

  /// 停止语音输入
  /// 
  /// 用户松开按钮时调用：
  /// 1. 通知上层停止录音
  /// 2. 停止流式语音服务
  /// 3. 获取后端返回的最终结果（识别文本 + 任务结构化数据）
  Future<void> _stopListening() async {
    widget.onVoiceInputEnd?.call({});
    
    try {
      final result = await _voiceService.stopListening();
      // 将结果传递给上层处理
      widget.onVoiceInputEnd?.call(result);
    } catch (e) {
      print("Failed to stop listening: $e");
    }
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
          // 长按开始语音输入
          onLongPressStart: (_) => _startListening(),
          // 松开结束语音输入
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
