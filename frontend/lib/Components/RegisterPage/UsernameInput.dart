import 'package:flutter/material.dart';

/// 用户名输入组件
///
/// 负责：
/// - 显示用户名输入框
/// - 处理用户名输入状态
class UsernameInput extends StatelessWidget {
  /// 控制器
  final TextEditingController controller;

  /// 焦点节点
  final FocusNode focusNode;

  /// 是否禁用
  final bool enabled;

  /// 下一个焦点节点
  final FocusNode? nextFocusNode;

  const UsernameInput({
    super.key,
    required this.controller,
    required this.focusNode,
    required this.enabled,
    this.nextFocusNode,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      focusNode: focusNode,
      enabled: enabled,
      decoration: InputDecoration(
        labelText: '用户名',
        hintText: '请输入用户名（至少3位）',
        prefixIcon: const Icon(Icons.person),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        filled: true,
        fillColor: Colors.grey.withValues(alpha: 0.1),
      ),
      textInputAction: TextInputAction.next,
      onSubmitted: (_) => nextFocusNode?.requestFocus(),
    );
  }
}