import 'package:flutter/material.dart';
import 'package:reminder/Route/main.dart';
import 'package:reminder/Stores/TaskManager.dart';
import 'package:reminder/Stores/LoginManager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await loginManager.init();
  final userId = await loginManager.logout();
  
  await taskManager.init();
  await taskManager.clearTasks(userId);
  
  runApp(getRootWidget());
}