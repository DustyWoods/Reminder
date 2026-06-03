import 'package:flutter/material.dart';
import 'package:reminder/Components/HomePage/LoginButton.dart';

/// 未登录视图组件
///
/// 负责：
/// - 显示未登录时的界面
/// - 提供登录入口
class UnauthenticatedView extends StatelessWidget {
  /// 登录成功回调
  final VoidCallback onLoginSuccess;

  const UnauthenticatedView({
    super.key,
    required this.onLoginSuccess,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      child: LoginButton(onLoginSuccess: onLoginSuccess),
    );
  }
}