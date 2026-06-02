import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/Stores/LoginManager.dart';

/// 登录页面
///
/// 负责：
/// - 显示登录界面
/// - 处理用户登录操作
/// - 登录成功后返回主页
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  /// 用户名输入控制器
  final TextEditingController _usernameController = TextEditingController();
  
  /// 密码输入控制器
  final TextEditingController _passwordController = TextEditingController();
  
  /// 是否正在登录
  bool _isLoggingIn = false;
  
  /// 用户名焦点节点
  final FocusNode _usernameFocus = FocusNode();
  
  /// 密码焦点节点
  final FocusNode _passwordFocus = FocusNode();

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _usernameFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  /// 处理登录操作
  Future<void> _handleLogin() async {
    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();
    
    if (username.isEmpty || password.isEmpty) {
      _showError('请输入用户名和密码');
      return;
    }
    
    setState(() => _isLoggingIn = true);
    
    try {
      // 调用登录 API
      final success = await loginManager.login(username, password);
      
      if (success) {
        // 登录成功，返回主页
        if (mounted) {
          Navigator.of(context).pop(true);
        }
      } else {
        _showError('用户名或密码错误');
      }
    } catch (e) {
      _showError('登录出错: $e');
    } finally {
      if (mounted) {
        setState(() => _isLoggingIn = false);
      }
    }
  }

  /// 跳转到注册页面
  void _navigateToRegister() {
    Navigator.pushNamed(context, '/register').then((result) {
      // 如果注册成功，提示用户可以登录
      if (result == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('注册成功，请登录'),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 2),
          ),
        );
      }
    });
  }

  /// 显示错误提示
  void _showError(String message) {
    if (!mounted) return;
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('登录'),
        backgroundColor: const Color.fromARGB(255, 47, 98, 209),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Logo 区域
              SizedBox(
                height: ScreenSize.getHeight(context) * 0.2,
                child: Center(
                  child: Icon(
                    Icons.task_alt,
                    size: 80,
                    color: const Color.fromARGB(255, 47, 98, 209),
                  ),
                ),
              ),
              
              const SizedBox(height: 40),
              
              // 用户名输入框
              TextField(
                controller: _usernameController,
                focusNode: _usernameFocus,
                enabled: !_isLoggingIn,
                decoration: InputDecoration(
                  labelText: '用户名',
                  hintText: '请输入用户名',
                  prefixIcon: const Icon(Icons.person),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                  fillColor: Colors.grey.withValues(alpha: 0.1),
                ),
                textInputAction: TextInputAction.next,
                onSubmitted: (_) => _passwordFocus.requestFocus(),
              ),
              
              const SizedBox(height: 20),
              
              // 密码输入框
              TextField(
                controller: _passwordController,
                focusNode: _passwordFocus,
                enabled: !_isLoggingIn,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: '密码',
                  hintText: '请输入密码',
                  prefixIcon: const Icon(Icons.lock),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                  fillColor: Colors.grey.withValues(alpha: 0.1),
                ),
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _handleLogin(),
              ),
              
              const SizedBox(height: 40),
              
              // 登录按钮
              SizedBox(
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoggingIn ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color.fromARGB(255, 47, 98, 209),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 2,
                  ),
                  child: _isLoggingIn
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Text(
                        '登录',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                ),
              ),
              
              const SizedBox(height: 20),
              
              // 注册入口
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '还没有账号？',
                    style: TextStyle(
                      color: Colors.grey.withValues(alpha: 0.7),
                      fontSize: 14,
                    ),
                  ),
                  TextButton(
                    onPressed: _isLoggingIn ? null : _navigateToRegister,
                    child: const Text(
                      '立即注册',
                      style: TextStyle(
                        color: Color.fromARGB(255, 47, 98, 209),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}