import 'package:flutter/material.dart';

/// 标题区域组件
///
/// 负责：
/// - 显示注册页面标题
class TitleSection extends StatelessWidget {
  const TitleSection({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text(
        '创建新账号',
        style: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.bold,
          color: Colors.black87,
        ),
      ),
    );
  }
}