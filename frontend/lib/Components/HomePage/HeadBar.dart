import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/stores/LoginManager.dart';
import 'package:reminder/stores/TaskManager.dart';
import 'package:reminder/api/AuthService.dart';

class HeadBar extends StatelessWidget {
  final VoidCallback? onLogoutSuccess;

  const HeadBar({super.key, this.onLogoutSuccess});

  void _showUserMenu(BuildContext context) {
    showMenu(
      context: context,
      position: RelativeRect.fromLTRB(
        ScreenSize.getWidth(context),
        ScreenSize.getTopInset(context) + 100,
        20,
        0,
      ),
      items: [
        PopupMenuItem(
          child: const Row(
            children: [
              Icon(Icons.logout, color: Colors.black87, size: 20),
              SizedBox(width: 10),
              Text('退出登录'),
            ],
          ),
          onTap: () => _showLogoutDialog(context),
        ),
        PopupMenuItem(
          child: const Row(
            children: [
              Icon(Icons.delete, color: Colors.red, size: 20),
              SizedBox(width: 10),
              Text('注销账号', style: TextStyle(color: Colors.red)),
            ],
          ),
          onTap: () => _showDeleteAccountDialog(context),
        ),
      ],
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认退出'),
        content: const Text('确定要退出登录吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              
              final userId = await loginManager.logout();
              await taskManager.clearTasks(userId);
              
              onLogoutSuccess?.call();
            },
            child: const Text(
              '确定',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }

  void _showDeleteAccountDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认注销账号'),
        content: const Text('此操作将永久删除您的账号和所有数据，且无法恢复。确定要继续吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);

              if (!loginManager.isInitialized()) {
                await loginManager.init();
              }

              final userId = loginManager.getUserId();
              if (userId != null) {
                try {
                  await AuthService.deleteUser(int.parse(userId));
                } catch (e) {
                  print('Delete account error: $e');
                }
              }
              
              await loginManager.logout();
              await taskManager.clearTasks(userId);
              
              onLogoutSuccess?.call();
            },
            child: const Text(
              '确定注销',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: ScreenSize.getWidth(context),
      decoration: BoxDecoration(
        color: Colors.transparent,
        border: Border(
          bottom: BorderSide(
            color: const Color.fromARGB(255, 18, 53, 131).withValues(alpha: 0.5),
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          GestureDetector(
            onTap: () => Navigator.pushNamed(context, '/calendar'),
            child: Container(
              margin: const EdgeInsets.only(left: 20),
              child: const Icon(
                Icons.calendar_month,
                color: Color.fromARGB(255, 29, 99, 204),
                size: 40,
              ),
            ),
          ),
          GestureDetector(
            onTap: () => _showUserMenu(context),
            child: Container(
              margin: const EdgeInsets.only(right: 20),
              child: const Icon(
                Icons.account_circle,
                color: Color.fromARGB(255, 2, 69, 170),
                size: 40,
              ),
            ),
          ),
        ],
      ),
    );
  }
}