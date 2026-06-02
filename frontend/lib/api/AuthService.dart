import 'package:dio/dio.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/Dio.dart';

class AuthService {
  static final DioUtils _dioUtils = DioUtils();

  static Future<Map<String, dynamic>> register(String username, String password) async {
    Response response = await _dioUtils.post(
      HttpConstants.REGISTER,
      data: {
        'username': username,
        'password': password,
      },
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> login(String username, String password) async {
    Response response = await _dioUtils.post(
      HttpConstants.LOGIN,
      data: {
        'username': username,
        'password': password,
      },
    );
    return response.data;
  }
}