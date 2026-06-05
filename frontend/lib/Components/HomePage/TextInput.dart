import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/api/TextService.dart';
import 'package:reminder/Stores/LoginManager.dart';

/// 文本输入组件
///
/// 负责：
/// - 显示文本输入框（布局与语音输入框一致）
/// - 支持多行输入和滚动
/// - 当有文字输入时显示发送按钮
/// - 点击发送按钮进行发送操作
class TextInput extends StatefulWidget {
  /// 发送成功回调
  final Function(Map<String, dynamic>) onSendSuccess;
  
  /// 发送失败回调
  final Function(String) onSendError;

  const TextInput({
    super.key,
    required this.onSendSuccess,
    required this.onSendError,
  });

  @override
  State<TextInput> createState() => _TextInputState();
}

class _TextInputState extends State<TextInput> {
  /// 文本控制器
  final TextEditingController _controller = TextEditingController();
  
  /// 是否正在发送
  bool _isSending = false;
  
  /// 是否有输入
  bool get _hasInput => _controller.text.trim().isNotEmpty;
  
  /// 输入框焦点节点
  final FocusNode _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  /// 处理发送操作
  Future<void> _handleSend() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _isSending) return;
    
    setState(() => _isSending = true);
    
    try {
      if (!loginManager.isInitialized()) {
        await loginManager.init();
      }
      // 获取当前登录用户的ID
      final userId = loginManager.getUserId();
      final int? userIdInt = userId != null ? int.tryParse(userId) : null;
      
      // 调用后端接口，传递用户ID
      final result = await TextService.getTask(text, userId: userIdInt);
      _controller.clear();
      widget.onSendSuccess(result);
    } catch (e) {
      widget.onSendError(e.toString());
    } finally {
      if (mounted) {
        setState(() => _isSending = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    const maxHeight = 140.0;
    const inputWidth = 45.0;
    
    return Positioned(
      bottom: ScreenSize.getBottomInset(context) + 20,
      right: ScreenSize.getWidth(context) * 0.1,
      width: ScreenSize.getWidth(context) * 0.8,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
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
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            // 左侧间距（模拟切换按钮位置）
            Container(
              width: inputWidth,
              color: Colors.transparent,
            ),
            
            // 输入框区域
            Expanded(
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  minHeight: 60,
                  maxHeight: maxHeight,
                ),
                child: SingleChildScrollView(
                  reverse: true,
                  child: TextField(
                    controller: _controller,
                    focusNode: _focusNode,
                    enabled: !_isSending,
                    maxLines: null,
                    minLines: 1,
                    keyboardType: TextInputType.multiline,
                    decoration: InputDecoration(
                      hintText: '输入任务内容...',
                      hintStyle: TextStyle(
                        color: Colors.grey.withValues(alpha: 0.5),
                      ),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 15,
                      ),
                    ),
                    onChanged: (_) => setState(() {}),
                    onSubmitted: (_) => _handleSend(),
                  ),
                ),
              ),
            ),
            
            // 发送按钮（固定在底部）
            Padding(
              padding: const EdgeInsets.only(bottom: 5, right: 5),
              child: AnimatedOpacity(
                opacity: _hasInput || _isSending ? 1.0 : 0.0,
                duration: const Duration(milliseconds: 200),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: _hasInput || _isSending ? 50 : 0,
                  height: 50,
                  child: _hasInput || _isSending
                    ? GestureDetector(
                        onTap: _isSending ? null : _handleSend,
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: _isSending 
                              ? Colors.grey 
                              : const Color.fromARGB(255, 47, 98, 209),
                            borderRadius: BorderRadius.circular(25),
                          ),
                          child: _isSending
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(
                                    Colors.white,
                                  ),
                                ),
                              )
                            : Icon(
                                Icons.send,
                                size: 24,
                                color: Colors.white,
                              ),
                        ),
                      )
                    : null,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
