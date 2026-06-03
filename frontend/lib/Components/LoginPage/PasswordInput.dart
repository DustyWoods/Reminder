import 'package:flutter/material.dart';

/// 密码输入组件
///
/// 负责：
/// - 显示密码输入框
/// - 处理密码输入状态
class PasswordInput extends StatelessWidget {
  /// 控制器
  final TextEditingController controller;

  /// 焦点节点
  final FocusNode focusNode;

  /// 是否禁用
  final bool enabled;

  /// 提交回调
  final VoidCallback? onSubmitted;

  const PasswordInput({
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
        labelText: '密码',
        hintText: '请输入密码',
        prefixIcon: const Icon(Icons.lock),
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