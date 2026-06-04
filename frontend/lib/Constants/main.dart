class GlobalConstants {
  static const String BASE_URL = 'http://10.0.2.2:8000';
  static const int TIME_OUT = 10;
  static const String TASKS_KEY = 'tasks';
}

class HomePageConstants {
  static const bool VOICE_INPUT = true;
  static const bool TEXT_INPUT = false;
}

enum calendarView {
  year,
  month,
  day,
  schedule,
}

class HttpConstants {
  static const String TEXT_TASK = '/api/text';
  
  static const String VOICE_START = '/api/voice/start';
  static const String VOICE_AUDIO = '/api/voice/audio';
  static const String VOICE_STOP = '/api/voice/stop';
  static const String VOICE_CANCEL = '/api/voice/cancel';
  
  static const String LOGIN = '/api/auth/login';
  static const String REGISTER = '/api/auth/register';
  static const String DELETE_USER = '/api/auth/delete';
}