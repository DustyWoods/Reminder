
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Viewmodels/task.dart';

class TokenManager {
  List<Task> _tasks = [];

  Future<SharedPreferences> _getInstance() async {
    return await SharedPreferences.getInstance();
  }

  Future<void> init() async {
    final prefs = await _getInstance();
    
    final taskCount = prefs.getInt('${GlobalConstants.TASKS_KEY}_count') ?? 0;
    if (taskCount > 0) {
      _tasks = [];
      for (int i = 0; i < taskCount; i++) {
        final taskJson = prefs.getString('${GlobalConstants.TASKS_KEY}_$i');
        if (taskJson != null) {
          final Map<String, dynamic> decoded = jsonDecode(taskJson);
          _tasks.add(Task.fromJson(decoded));
        }
      }
    }
  }

  Future<void> _saveSingleTask(int index, Task task) async {
    final prefs = await _getInstance();
    final taskJson = jsonEncode({
      'title': task.title,
      'description': task.description,
      'dueDate': task.dueDate,
      'isCompleted': task.isCompleted,
    });
    await prefs.setString('${GlobalConstants.TASKS_KEY}_$index', taskJson);
    await prefs.setInt('${GlobalConstants.TASKS_KEY}_count', _tasks.length);
  }

  List<Task> getTasks() {
    return _tasks;
  }

  Future<void> addTask(Task task) async {
    _tasks.add(task);
    await _saveSingleTask(_tasks.length - 1, task);
  }

  Future<void> updateTask(int index, Task task) async {
    if (index >= 0 && index < _tasks.length) {
      _tasks[index] = task;
      await _saveSingleTask(index, task);
    }
  }

  Future<void> removeTask(int index) async {
    if (index >= 0 && index < _tasks.length) {
      _tasks.removeAt(index);
      final prefs = await _getInstance();
      await prefs.setInt('${GlobalConstants.TASKS_KEY}_count', _tasks.length);
      for (int i = index; i < _tasks.length; i++) {
        final taskJson = jsonEncode({
          'title': _tasks[i].title,
          'description': _tasks[i].description,
          'dueDate': _tasks[i].dueDate,
          'isCompleted': _tasks[i].isCompleted,
        });
        await prefs.setString('${GlobalConstants.TASKS_KEY}_$i', taskJson);
      }
      await prefs.remove('${GlobalConstants.TASKS_KEY}_${_tasks.length}');
    }
  }

  Future<void> removeToken() async {
    final prefs = await _getInstance();
    final count = prefs.getInt('${GlobalConstants.TASKS_KEY}_count') ?? 0;
    for (int i = 0; i < count; i++) {
      await prefs.remove('${GlobalConstants.TASKS_KEY}_$i');
    }
    await prefs.remove('${GlobalConstants.TASKS_KEY}_count');
    await prefs.remove(GlobalConstants.TASKS_KEY);
    _tasks = [];
  }
}

final tokenManager = TokenManager();