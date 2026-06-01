class GlobalConstants {
  static const String BASE_URL = 'http://10.0.2.2:8000';
  static const int TIME_OUT = 10;
  static const String TASKS_KEY = 'tasks';

  static const bool VOICE_INPUT = true;
  static const bool TEXT_INPUT = false;
}

class HttpConstants {
  static const String TEXT_TASK = '/api/text';
  
  // 语音识别相关路由
  static const String VOICE_START = '/api/voice/start';
  static const String VOICE_AUDIO = '/api/voice/audio';
  static const String VOICE_STOP = '/api/voice/stop';
  static const String VOICE_CANCEL = '/api/voice/cancel';
  
  // 登录相关路由
  static const String LOGIN = '/api/auth/login';
  static const String REGISTER = '/api/auth/register';
  static const String LOGOUT = '/api/auth/logout';
  static const String CHECK_AUTH = '/api/auth/check';
}