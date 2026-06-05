import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Viewmodels/task.dart';
import 'package:reminder/Stores/LoginManager.dart';
import 'package:reminder/api/TaskService.dart';

class TaskManager {
  List<Task> _tasks = [];
  late SharedPreferences _prefs;
  bool _isInitialized = false;
  
  String _getUserTasksKey([String? userId]) {
    final effectiveUserId = userId ?? loginManager.getUserId() ?? 'default';
    return '${GlobalConstants.TASKS_KEY}_$effectiveUserId';
  }

  Future<void> init() async {
    if (_isInitialized) return;
    
    _prefs = await SharedPreferences.getInstance();
    
    final taskCount = _prefs.getInt('${_getUserTasksKey()}_count') ?? 0;
    if (taskCount > 0) {
      _tasks = [];
      for (int i = 0; i < taskCount; i++) {
        final taskJson = _prefs.getString('${_getUserTasksKey()}_$i');
        if (taskJson != null) {
          final Map<String, dynamic> decoded = jsonDecode(taskJson);
          _tasks.add(Task.fromJson(decoded));
        }
      }
    }
    
    _isInitialized = true;
  }
  
  bool isInitialized() => _isInitialized;

  Future<void> _saveSingleTask(int index, Task task) async {
    if (!_isInitialized) await init();
    
    final taskJson = jsonEncode(task.toJson());
    await _prefs.setString('${_getUserTasksKey()}_$index', taskJson);
    await _prefs.setInt('${_getUserTasksKey()}_count', _tasks.length);
  }

  List<Task> getTasks() {
    return _tasks;
  }

  Future<void> addTask(Task task) async {
    if (!_isInitialized) await init();
    
    _tasks.add(task);
    await _saveSingleTask(_tasks.length - 1, task);
  }

  Future<void> updateTask(int index, Task task) async {
    if (!_isInitialized) await init();
    
    if (index >= 0 && index < _tasks.length) {
      _tasks[index] = task;
      await _saveSingleTask(index, task);
    }
  }

  Future<void> removeTask(int index) async {
    if (!_isInitialized) await init();
    
    if (index >= 0 && index < _tasks.length) {
      final task = _tasks[index];
      
      if (loginManager.isLoggedIn()) {
        final userId = loginManager.getUserId();
        if (userId != null && task.id != null) {
          _deleteTaskInBackground(int.parse(userId), task.id!);
        }
      }
      
      _tasks.removeAt(index);
      await _prefs.setInt('${_getUserTasksKey()}_count', _tasks.length);
      for (int i = index; i < _tasks.length; i++) {
        final taskJson = jsonEncode(_tasks[i].toJson());
        await _prefs.setString('${_getUserTasksKey()}_$i', taskJson);
      }
      await _prefs.remove('${_getUserTasksKey()}_${_tasks.length}');
    }
  }
  
  void _deleteTaskInBackground(int userId, int taskId) {
    TaskService.deleteTask(userId, taskId).catchError((e) {
      print('Error deleting task from server: $e');
    });
  }

  Future<void> clearTasks([String? userId]) async {
    if (!_isInitialized) {
      _prefs = await SharedPreferences.getInstance();
    }
    
    final userTasksKey = _getUserTasksKey(userId);
    final count = _prefs.getInt('${userTasksKey}_count') ?? 0;
    for (int i = 0; i < count; i++) {
      await _prefs.remove('${userTasksKey}_$i');
    }
    await _prefs.remove('${userTasksKey}_count');
    await _prefs.remove(userTasksKey);
    _tasks = [];
  }
}

final taskManager = TaskManager();