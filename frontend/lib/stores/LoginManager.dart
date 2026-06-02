import 'package:shared_preferences/shared_preferences.dart';
import 'package:reminder/api/AuthService.dart';

class LoginManager {
  final String _isLoggedInKey = 'is_logged_in';
  final String _userIdKey = 'user_id';
  final String _userNameKey = 'user_name';
  
  late SharedPreferences _prefs;
  bool _isInitialized = false;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    _isInitialized = true;
  }
  
  bool isInitialized() => _isInitialized;
  
  bool isLoggedIn() {
    if (!_isInitialized) return false;
    return _prefs.getBool(_isLoggedInKey) ?? false;
  }
  
  String? getUserId() {
    if (!_isInitialized) return null;
    return _prefs.getString(_userIdKey);
  }
  
  String? getUserName() {
    if (!_isInitialized) return null;
    return _prefs.getString(_userNameKey);
  }

  Future<bool> login(String username, String password) async {
    if (!_isInitialized) return false;
    
    try {
      final result = await AuthService.login(username, password);
      
      if (result['success'] == true) {
        await _prefs.setBool(_isLoggedInKey, true);
        await _prefs.setString(_userIdKey, result['user']['id'].toString());
        await _prefs.setString(_userNameKey, result['user']['username']);
        
        return true;
      } else {
        return false;
      }
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }

  Future<bool> register(String username, String password) async {
    if (!_isInitialized) return false;
    
    try {
      final result = await AuthService.register(username, password);
      
      return result['success'] == true;
    } catch (e) {
      print('Register error: $e');
      return false;
    }
  }

  Future<String?> logout() async {
    if (!_isInitialized) return null;
    
    final userId = _prefs.getString(_userIdKey);
    
    await _prefs.setBool(_isLoggedInKey, false);
    await _prefs.remove(_userIdKey);
    await _prefs.remove(_userNameKey);
    
    return userId;
  }
}

final loginManager = LoginManager();