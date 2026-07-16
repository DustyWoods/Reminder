import 'package:flutter/material.dart';
import 'package:reminder/Components/HomePage/HeadBar.dart';
import 'package:reminder/Components/HomePage/Greet.dart';
import 'package:reminder/Components/HomePage/TaskBar.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/Viewmodels/task.dart';

/// 主内容组件
///
/// 负责：
/// - 显示已登录时的主内容区域
/// - 包含顶部栏、问候语和任务列表
class MainContent extends StatelessWidget {
  /// 退出登录成功回调
  final VoidCallback onLogoutSuccess;

  /// 是否已初始化
  final bool isInitialized;

  /// 任务列表
  final List<Task> tasks;

  /// 删除任务回调（接收任务ID）
  final Function(int) onDeleteTask;

  const MainContent({
    super.key,
    required this.onLogoutSuccess,
    required this.isInitialized,
    required this.tasks,
    required this.onDeleteTask,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: ScreenSize.getHeight(context) - 80,
      child: Container(
        color: Colors.white,
        alignment: Alignment.center,
        child: Column(
          children: [
            SizedBox(
              height: 50,
              child: HeadBar(onLogoutSuccess: onLogoutSuccess),
            ),
            // 问候语区域
            SizedBox(
              height: ScreenSize.getHeight(context) * 0.15,
              child: const Greet(),
            ),
            // 任务列表区域
            SizedBox(
              height: ScreenSize.getHeight(context) * 0.65,
              child: isInitialized
                ? TaskBar(tasks: tasks, onDeleteTask: onDeleteTask)
                : const Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      ),
    );
  }
}