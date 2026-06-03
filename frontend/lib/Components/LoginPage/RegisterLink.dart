import 'package:flutter/material.dart';

/// 注册链接组件
///
/// 负责：
/// - 显示注册入口链接
/// - 点击后跳转到注册页面
class RegisterLink extends StatelessWidget {
  /// 是否禁用
  final bool enabled;

  /// 点击回调
  final VoidCallback? onPressed;

  const RegisterLink({
    super.key,
    required this.enabled,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          '还没有账号？',
          style: TextStyle(
            color: Colors.grey.withValues(alpha: 0.7),
            fontSize: 14,
          ),
        ),
        TextButton(
          onPressed: enabled ? onPressed : null,
          child: const Text(
            '立即注册',
            style: TextStyle(
              color: Color.fromARGB(255, 47, 98, 209),
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }
}