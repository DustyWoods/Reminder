import 'package:dio/dio.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/Dio.dart';

class TaskService {
  static final DioUtils _dioUtils = DioUtils();

  static Future<Map<String, dynamic>> deleteTask(int userId, int taskId) async {
    Response response = await _dioUtils.delete(
      '${HttpConstants.TASKS}/$userId/$taskId',
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> getAllTasks(int userId) async {
    Response response = await _dioUtils.get(
      '${HttpConstants.TASKS}/$userId',
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> getTask(int userId, int taskId) async {
    Response response = await _dioUtils.get(
      '${HttpConstants.TASKS}/$userId/$taskId',
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> createTask(
    int userId,
    String title,
    String dueDate,
    String description,
  ) async {
    Response response = await _dioUtils.post(
      '${HttpConstants.TASKS}/$userId',
      data: {
        'title': title,
        'due_date': dueDate,
        'description': description,
      },
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> updateTask(
    int userId,
    int taskId, {
    String? title,
    String? dueDate,
    String? description,
    bool? completed,
  }) async {
    Map<String, dynamic> data = {};
    if (title != null) data['title'] = title;
    if (dueDate != null) data['due_date'] = dueDate;
    if (description != null) data['description'] = description;
    if (completed != null) data['completed'] = completed;

    Response response = await _dioUtils.put(
      '${HttpConstants.TASKS}/$userId/$taskId',
      data: data,
    );
    return response.data;
  }
}
