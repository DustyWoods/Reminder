import 'package:dio/dio.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/Dio.dart';

/// 认证服务类
///
/// 负责：
/// - 用户注册
/// - 用户登录
/// - 用户登出
/// - 检查认证状态
class AuthService {
  static final DioUtils _dioUtils = DioUtils();

  /// 用户注册
  /// 
  /// Args:
  ///   username: 用户名
  ///   password: 密码
  /// 
  /// Returns:
  ///   Map: {
  ///     "success": bool,
  ///     "message": String,
  ///     "user": {"id": int, "username": String}?
  ///   }
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

  /// 用户登录
  /// 
  /// Args:
  ///   username: 用户名
  ///   password: 密码
  /// 
  /// Returns:
  ///   Map: {
  ///     "success": bool,
  ///     "message": String,
  ///     "user": {"id": int, "username": String}?,
  ///     "token": String?
  ///   }
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

  /// 用户登出
  /// 
  /// Args:
  ///   token: 用户 token
  /// 
  /// Returns:
  ///   Map: {
  ///     "success": bool,
  ///     "message": String
  ///   }
  static Future<Map<String, dynamic>> logout(String token) async {
    Response response = await _dioUtils.post(
      HttpConstants.LOGOUT,
      data: {},
    );
    return response.data;
  }

  /// 检查认证状态
  /// 
  /// Args:
  ///   token: 用户 token
  /// 
  /// Returns:
  ///   Map: {
  ///     "success": bool,
  ///     "message": String,
  ///     "user": {"id": int, "username": String}?,
  ///     "token": String?
  ///   }
  static Future<Map<String, dynamic>> checkAuth(String token) async {
    Response response = await _dioUtils.post(
      HttpConstants.CHECK_AUTH,
      data: {},
    );
    return response.data;
  }
}