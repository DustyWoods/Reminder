import 'package:flutter/material.dart';

/// 确认密码输入组件
///
/// 负责：
/// - 显示确认密码输入框
/// - 处理确认密码输入状态
class ConfirmPasswordInput extends StatelessWidget {
  /// 控制器
  final TextEditingController controller;

  /// 焦点节点
  final FocusNode focusNode;

  /// 是否禁用
  final bool enabled;

  /// 提交回调
  final VoidCallback? onSubmitted;

  const ConfirmPasswordInput({
    super.key,
    required this.controller,
    required this.focusNode,
    required this.enabled,
    this.onSubmitted,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      focusNode: focusNode,
      enabled: enabled,
      obscureText: true,
      decoration: InputDecoration(
        labelText: '确认密码',
        hintText: '请再次输入密码',
        prefixIcon: const Icon(Icons.lock_outline),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        filled: true,
        fillColor: Colors.grey.withValues(alpha: 0.1),
      ),
      textInputAction: TextInputAction.done,
      onSubmitted: (_) => onSubmitted?.call(),
    );
  }
}