import 'package:flutter/material.dart';

/// 加载视图组件
///
/// 负责：
/// - 显示应用初始化时的加载动画
class LoadingView extends StatelessWidget {
  const LoadingView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: CircularProgressIndicator(),
    );
  }
}