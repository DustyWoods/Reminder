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
}
