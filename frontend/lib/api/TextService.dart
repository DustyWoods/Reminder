import 'package:dio/dio.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/Dio.dart';

class TextService {
  static final DioUtils _dioUtils = DioUtils();

  /// 智能任务处理 - 自动识别操作类型
  static Future<Map<String, dynamic>> processText(String text, {int? userId}) async {
    Response response = await _dioUtils.post(
      HttpConstants.TEXT_TASK,
      data: {'text': text},
      queryParameters: userId != null ? {'user_id': userId} : null,
    );
    return response.data;
  }

  /// 创建任务
  static Future<Map<String, dynamic>> createTask(String text, {int? userId}) async {
    Response response = await _dioUtils.post(
      '${HttpConstants.TEXT_TASK}/create',
      data: {'text': text},
      queryParameters: userId != null ? {'user_id': userId} : null,
    );
    return response.data;
  }

  /// 更新任务
  static Future<Map<String, dynamic>> updateTask(String text, {int? userId, int? taskId}) async {
    Response response = await _dioUtils.post(
      '${HttpConstants.TEXT_TASK}/update',
      data: {'text': text},
      queryParameters: {
        if (userId != null) 'user_id': userId,
        if (taskId != null) 'task_id': taskId,
      },
    );
    return response.data;
  }

  /// 删除任务
  static Future<Map<String, dynamic>> deleteTask(String text, {int? userId, int? taskId}) async {
    Response response = await _dioUtils.post(
      '${HttpConstants.TEXT_TASK}/delete',
      data: {'text': text},
      queryParameters: {
        if (userId != null) 'user_id': userId,
        if (taskId != null) 'task_id': taskId,
      },
    );
    return response.data;
  }

  /// 查询任务
  static Future<Map<String, dynamic>> queryTasks({int? userId}) async {
    Response response = await _dioUtils.post(
      '${HttpConstants.TEXT_TASK}/query',
      data: {},
      queryParameters: userId != null ? {'user_id': userId} : null,
    );
    return response.data;
  }

  /// 解析API响应并返回操作类型
  static String getOperationType(Map<String, dynamic> response) {
    return response['operation'] ?? 'create';
  }

  /// 检查操作是否成功
  static bool isSuccess(Map<String, dynamic> response) {
    return response['success'] ?? false;
  }

  /// 获取操作消息
  static String getMessage(Map<String, dynamic> response) {
    return response['message'] ?? '';
  }

  /// 获取任务列表
  static List<dynamic> getTasks(Map<String, dynamic> response) {
    return response['tasks'] ?? [];
  }
}
