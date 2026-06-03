import 'package:flutter/material.dart';

/// 返回登录链接组件
///
/// 负责：
/// - 显示返回登录入口链接
/// - 点击后返回登录页面
class LoginLink extends StatelessWidget {
  /// 是否禁用
  final bool enabled;

  /// 点击回调
  final VoidCallback? onPressed;

  const LoginLink({
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
          '已有账号？',
          style: TextStyle(
            color: Colors.grey.withValues(alpha: 0.7),
            fontSize: 14,
          ),
        ),
        TextButton(
          onPressed: enabled ? onPressed : null,
          child: const Text(
            '返回登录',
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