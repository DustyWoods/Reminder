import 'package:dio/dio.dart';

import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/Dio.dart';

class TextService {
  static final DioUtils _dioUtils = DioUtils();

  static Future<Map<String, dynamic>> getTask(String text) async {
    Response response = await _dioUtils.post(HttpConstants.TEXT_TASK, data: {'text': text});
    return response.data;
  }
}
