import 'package:dio/dio.dart';
import 'package:reminder/Constants/main.dart';

class DioUtils {
  final Dio _dio = Dio();

  DioUtils() {
    _dio.options.baseUrl = GlobalConstants.BASE_URL;
    _dio.options.connectTimeout = const Duration(seconds: GlobalConstants.TIME_OUT);
    _dio.options.receiveTimeout = const Duration(seconds: GlobalConstants.TIME_OUT);

    _addInterceptor();
  }

  void _addInterceptor() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        handler.next(options);
      },
      onResponse: (response, handler) {
        handler.next(response);
      },
      onError: (error, handler) {
        handler.next(error);
      },
    ));
  }

  /// 发送普通 POST 请求
  Future<Response> post(String url, {Map<String, dynamic>? data, Map<String, dynamic>? queryParameters}) async {
    return await _dio.post(url, data: data, queryParameters: queryParameters);
  }

  /// 发送二进制数据 POST 请求
  Future<Response> postBinary(String url, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return await _dio.post(
      url,
      data: data,
      queryParameters: queryParameters,
      options: options ?? Options(headers: {'Content-Type': 'application/octet-stream'}),
    );
  }

  /// 发送 DELETE 请求
  Future<Response> delete(String url, {Map<String, dynamic>? data}) async {
    return await _dio.delete(url, data: data);
  }
}
