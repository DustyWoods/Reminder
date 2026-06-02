import 'package:flutter/material.dart';
import 'package:reminder/Route/main.dart';
import 'package:reminder/Stores/TaskManager.dart';
import 'package:reminder/Stores/LoginManager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final userId = await loginManager.logout();
  await taskManager.clearTasks(userId);
  
  runApp(getRootWidget());
}