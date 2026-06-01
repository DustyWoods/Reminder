import 'package:flutter/material.dart';

/// 登录按钮组件
///
/// 负责：
/// - 显示登录按钮
/// - 点击后跳转到登录页面
/// - 登录成功后触发回调
class LoginButton extends StatelessWidget {
  /// 登录成功回调
  final VoidCallback onLoginSuccess;

  const LoginButton({
    super.key,
    required this.onLoginSuccess,
  });

  /// 处理点击登录按钮
  void _handleLogin(BuildContext context) {
    // 使用路由跳转到登录页面
    Navigator.pushNamed(context, '/login').then((result) {
      // 登录成功后触发回调
      if (result == true) {
        onLoginSuccess();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Logo
          Icon(
            Icons.task_alt,
            size: 100,
            color: const Color.fromARGB(255, 47, 98, 209),
          ),
          
          const SizedBox(height: 30),
          
          // 提示文字
          Text(
            '欢迎使用 拾序',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          
          const SizedBox(height: 10),
          
          Text(
            '请登录以使用完整功能',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.withValues(alpha: 0.7),
            ),
          ),
          
          const SizedBox(height: 50),
          
          // 登录按钮
          GestureDetector(
            onTap: () => _handleLogin(context),
            child: Container(
              width: 200,
              height: 50,
              decoration: BoxDecoration(
                color: const Color.fromARGB(255, 47, 98, 209),
                borderRadius: BorderRadius.circular(25),
                boxShadow: [
                  BoxShadow(
                    color: const Color.fromARGB(255, 47, 98, 209).withValues(alpha: 0.3),
                    blurRadius: 10,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: const Center(
                child: Text(
                  '登录',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}