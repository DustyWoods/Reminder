import 'package:shared_preferences/shared_preferences.dart';
import 'package:reminder/api/AuthService.dart';

/// 登录状态管理器
///
/// 负责：
/// - 管理用户登录状态
/// - 存储和读取登录信息
/// - 提供登录/登出接口
class LoginManager {
  final String _isLoggedInKey = 'is_logged_in';
  final String _userIdKey = 'user_id';
  final String _userNameKey = 'user_name';
  final String _tokenKey = 'auth_token';
  
  late SharedPreferences _prefs;
  bool _isInitialized = false;
  
  /// 初始化登录管理器
  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    _isInitialized = true;
  }
  
  /// 检查是否已初始化
  bool isInitialized() => _isInitialized;
  
  /// 检查是否已登录
  bool isLoggedIn() {
    if (!_isInitialized) return false;
    return _prefs.getBool(_isLoggedInKey) ?? false;
  }
  
  /// 获取用户ID
  String? getUserId() {
    if (!_isInitialized) return null;
    return _prefs.getString(_userIdKey);
  }
  
  /// 获取用户名
  String? getUserName() {
    if (!_isInitialized) return null;
    return _prefs.getString(_userNameKey);
  }
  
  /// 获取 Token
  String? getToken() {
    if (!_isInitialized) return null;
    return _prefs.getString(_tokenKey);
  }
  
  /// 用户登录
  /// 
  /// Args:
  ///   username: 用户名
  ///   password: 密码
  /// 
  /// Returns:
  ///   Future<bool>: 登录是否成功
  Future<bool> login(String username, String password) async {
    if (!_isInitialized) return false;
    
    try {
      final result = await AuthService.login(username, password);
      
      if (result['success'] == true) {
        // 保存登录状态
        await _prefs.setBool(_isLoggedInKey, true);
        await _prefs.setString(_userIdKey, result['user']['id'].toString());
        await _prefs.setString(_userNameKey, result['user']['username']);
        
        // 保存 token
        if (result['token'] != null) {
          await _prefs.setString(_tokenKey, result['token']);
        }
        
        return true;
      } else {
        // 登录失败
        return false;
      }
    } catch (e) {
      // 网络错误或其他异常
      print('Login error: $e');
      return false;
    }
  }
  
  /// 用户注册
  /// 
  /// Args:
  ///   username: 用户名
  ///   password: 密码
  /// 
  /// Returns:
  ///   Future<bool>: 注册是否成功
  Future<bool> register(String username, String password) async {
    if (!_isInitialized) return false;
    
    try {
      final result = await AuthService.register(username, password);
      
      return result['success'] == true;
    } catch (e) {
      // 网络错误或其他异常
      print('Register error: $e');
      return false;
    }
  }
  
  /// 用户登出
  Future<void> logout() async {
    if (!_isInitialized) return;
    
    // 调用后端登出接口
    final token = getToken();
    if (token != null) {
      try {
        await AuthService.logout(token);
      } catch (e) {
        print('Logout error: $e');
      }
    }
    
    // 清除本地登录状态
    await _prefs.setBool(_isLoggedInKey, false);
    await _prefs.remove(_userIdKey);
    await _prefs.remove(_userNameKey);
    await _prefs.remove(_tokenKey);
  }
}

/// 全局登录管理器实例
final loginManager = LoginManager();