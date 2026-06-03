import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';

/// Logo区域组件
///
/// 负责：
/// - 显示应用Logo
class LogoSection extends StatelessWidget {
  const LogoSection({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: ScreenSize.getHeight(context) * 0.15,
      child: Center(
        child: Icon(
          Icons.task_alt,
          size: 80,
          color: const Color.fromARGB(255, 47, 98, 209),
        ),
      ),
    );
  }
}