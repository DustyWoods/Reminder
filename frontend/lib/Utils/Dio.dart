
import 'package:dio/dio.dart';
import 'package:reminder/constants/main.dart';

class DioUtils {
  final Dio _dio = Dio();

  DioUtils() {
    _dio.options.baseUrl = GlobalConstants.BASE_URL;
    _dio.options.connectTimeout = Duration(seconds:GlobalConstants.TIME_OUT);
    _dio.options.receiveTimeout = Duration(seconds:GlobalConstants.TIME_OUT);
    _dio.options.connectTimeout = Duration(seconds:GlobalConstants.TIME_OUT);

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

  Future<Response> post(String url, {Map<String, dynamic>? data}) async {
    return await _dio.post(url, data: data);
  }
}