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

  Future<void> _saveAllTasks() async {
    if (!_isInitialized) await init();
    
    await _prefs.setInt('${_getUserTasksKey()}_count', _tasks.length);
    for (int i = 0; i < _tasks.length; i++) {
      final taskJson = jsonEncode(_tasks[i].toJson());
      await _prefs.setString('${_getUserTasksKey()}_$i', taskJson);
    }
  }

  List<Task> getTasks() {
    return _tasks;
  }

  int getTaskCount() {
    return _tasks.length;
  }

  Task? getTaskById(int taskId) {
    return _tasks.firstWhere((task) => task.id == taskId, orElse: () => Task('', '', {}, id: -1));
  }
  
  bool hasTaskWithId(int taskId) {
    return _tasks.any((task) => task.id == taskId);
  }

  int getTaskIndexById(int taskId) {
    return _tasks.indexWhere((task) => task.id == taskId);
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

  Future<void> updateTaskById(int taskId, Task updatedTask) async {
    if (!_isInitialized) await init();
    
    final index = getTaskIndexById(taskId);
    if (index >= 0) {
      updatedTask.id = taskId;
      _tasks[index] = updatedTask;
      await _saveSingleTask(index, updatedTask);
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

  Future<void> removeTaskById(int taskId) async {
    if (!_isInitialized) await init();
    
    final index = getTaskIndexById(taskId);
    if (index >= 0) {
      await removeTask(index);
    }
  }
  
  void _deleteTaskInBackground(int userId, int taskId) {
    // 只有当任务ID有效时才调用后端删除
    if (taskId <= 0) {
      print('Skipping backend delete for invalid task ID: $taskId');
      return;
    }
    
    TaskService.deleteTask(userId, taskId).then((_) {
      // Task deleted successfully
    }).catchError((e) {
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

  /// 根据操作类型批量更新本地任务数据
  /// 
  /// operation: 操作类型 (create/update/delete/query/mixed)
  /// tasks: 任务列表
  /// 
  /// Returns: 操作是否成功
  Future<bool> syncTasksFromServer(String operation, List<dynamic> tasks) async {
    if (!_isInitialized) await init();
    
    try {
      switch (operation.toLowerCase()) {
        case 'create':
        case 'schedule':
          return await _handleCreateOperation(tasks);
        case 'update':
          return await _handleUpdateOperation(tasks);
        case 'delete':
          return await _handleDeleteOperation(tasks);
        case 'query':
          return await _handleQueryOperation(tasks);
        case 'mixed':
          // 混合操作：直接刷新本地数据
          return await _handleQueryOperation(tasks);
        default:
          print('Unknown operation type: $operation');
          return false;
      }
    } catch (e) {
      print('Error syncing tasks: $e');
      return false;
    }
  }

  /// 处理创建操作
  Future<bool> _handleCreateOperation(List<dynamic> tasks) async {
    for (var taskData in tasks) {
      try {
        Task task = Task.fromJson(taskData);
        // 验证任务是否有有效的ID（确保任务已保存到数据库）
        if (task.id == null || task.id! <= 0) {
          print('Skipping task without valid ID: ${task.title}');
          continue;
        }
        _tasks.add(task);
        print('Created task: ${task.title}, ID: ${task.id}');
      } catch (e) {
        print('Error creating task: $e');
        return false;
      }
    }
    await _saveAllTasks();
    return true;
  }

  /// 处理更新操作
  Future<bool> _handleUpdateOperation(List<dynamic> tasks) async {
    for (var taskData in tasks) {
      try {
        Task updatedTask = Task.fromJson(taskData);
        if (updatedTask.id != null) {
          final index = getTaskIndexById(updatedTask.id!);
          if (index >= 0) {
            _tasks[index] = updatedTask;
            print('Updated task: ${updatedTask.title}');
          } else {
            // 如果本地没有该任务，添加它
            _tasks.add(updatedTask);
            print('Added new task from update: ${updatedTask.title}');
          }
        }
      } catch (e) {
        print('Error updating task: $e');
        return false;
      }
    }
    await _saveAllTasks();
    return true;
  }

  /// 处理删除操作
  Future<bool> _handleDeleteOperation(List<dynamic> tasks) async {
    for (var taskData in tasks) {
      try {
        int taskId;
        if (taskData is Map) {
          taskId = taskData['id'] ?? taskData['task_id'];
        } else if (taskData is int) {
          taskId = taskData;
        } else {
          continue;
        }
        
        final index = getTaskIndexById(taskId);
        if (index >= 0) {
          _tasks.removeAt(index);
          print('Deleted task with id: $taskId');
        }
      } catch (e) {
        print('Error deleting task: $e');
        return false;
      }
    }
    await _saveAllTasks();
    return true;
  }

  /// 处理查询操作（用服务器数据替换本地数据）
  Future<bool> _handleQueryOperation(List<dynamic> tasks) async {
    _tasks.clear();
    
    for (var taskData in tasks) {
      try {
        Task task = Task.fromJson(taskData);
        _tasks.add(task);
      } catch (e) {
        print('Error parsing task from query: $e');
        return false;
      }
    }
    await _saveAllTasks();
    print('Synced ${_tasks.length} tasks from server');
    return true;
  }

  /// 刷新本地数据（从服务器重新获取所有任务）
  Future<void> refreshTasks() async {
    if (!loginManager.isLoggedIn()) return;
    
    final userId = loginManager.getUserId();
    if (userId != null) {
      try {
        final response = await TaskService.getAllTasks(int.parse(userId));
        final tasks = response['tasks'] as List<dynamic>;
        await _handleQueryOperation(tasks);
      } catch (e) {
        print('Error refreshing tasks: $e');
      }
    }
  }
}

final taskManager = TaskManager();
