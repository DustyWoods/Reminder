import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/stores/LoginManager.dart';

/// 注册页面
///
/// 负责：
/// - 显示注册界面
/// - 处理用户注册操作
/// - 注册成功后返回登录页面
class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  /// 用户名输入控制器
  final TextEditingController _usernameController = TextEditingController();
  
  /// 密码输入控制器
  final TextEditingController _passwordController = TextEditingController();
  
  /// 确认密码输入控制器
  final TextEditingController _confirmPasswordController = TextEditingController();
  
  /// 是否正在注册
  bool _isRegistering = false;
  
  /// 用户名焦点节点
  final FocusNode _usernameFocus = FocusNode();
  
  /// 密码焦点节点
  final FocusNode _passwordFocus = FocusNode();
  
  /// 确认密码焦点节点
  final FocusNode _confirmPasswordFocus = FocusNode();

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _usernameFocus.dispose();
    _passwordFocus.dispose();
    _confirmPasswordFocus.dispose();
    super.dispose();
  }

  /// 处理注册操作
  Future<void> _handleRegister() async {
    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();
    final confirmPassword = _confirmPasswordController.text.trim();
    
    if (username.isEmpty || password.isEmpty) {
      _showError('请输入用户名和密码');
      return;
    }
    
    if (password != confirmPassword) {
      _showError('两次输入的密码不一致');
      return;
    }
    
    if (password.length < 6) {
      _showError('密码长度至少为6位');
      return;
    }
    
    if (username.length < 3) {
      _showError('用户名长度至少为3位');
      return;
    }
    
    setState(() => _isRegistering = true);
    
    try {
      // 调用注册 API
      final success = await loginManager.register(username, password);
      
      if (success) {
        // 注册成功，弹出并返回 true 表示注册成功
        if (mounted) {
          Navigator.pop(context, true);
        }
      } else {
        _showError('注册失败，用户名可能已存在');
      }
    } catch (e) {
      _showError('注册出错: $e');
    } finally {
      if (mounted) {
        setState(() => _isRegistering = false);
      }
    }
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
        title: const Text('注册'),
        backgroundColor: const Color.fromARGB(255, 47, 98, 209),
        foregroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Logo 区域
              SizedBox(
                height: ScreenSize.getHeight(context) * 0.15,
                child: Center(
                  child: Icon(
                    Icons.task_alt,
                    size: 80,
                    color: const Color.fromARGB(255, 47, 98, 209),
                  ),
                ),
              ),
              
              const SizedBox(height: 20),
              
              // 标题
              const Center(
                child: Text(
                  '创建新账号',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ),
              
              const SizedBox(height: 30),
              
              // 用户名输入框
              TextField(
                controller: _usernameController,
                focusNode: _usernameFocus,
                enabled: !_isRegistering,
                decoration: InputDecoration(
                  labelText: '用户名',
                  hintText: '请输入用户名（至少3位）',
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
                enabled: !_isRegistering,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: '密码',
                  hintText: '请输入密码（至少6位）',
                  prefixIcon: const Icon(Icons.lock),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                  fillColor: Colors.grey.withValues(alpha: 0.1),
                ),
                textInputAction: TextInputAction.next,
                onSubmitted: (_) => _confirmPasswordFocus.requestFocus(),
              ),
              
              const SizedBox(height: 20),
              
              // 确认密码输入框
              TextField(
                controller: _confirmPasswordController,
                focusNode: _confirmPasswordFocus,
                enabled: !_isRegistering,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: '确认密码',
                  hintText: '请再次输入密码',
                  prefixIcon: const Icon(Icons.lock_outline),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                  fillColor: Colors.grey.withValues(alpha: 0.1),
                ),
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _handleRegister(),
              ),
              
              const SizedBox(height: 40),
              
              // 注册按钮
              SizedBox(
                height: 50,
                child: ElevatedButton(
                  onPressed: _isRegistering ? null : _handleRegister,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color.fromARGB(255, 47, 98, 209),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 2,
                  ),
                  child: _isRegistering
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Text(
                        '注册',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                ),
              ),
              
              const SizedBox(height: 20),
              
              // 返回登录提示
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '已有账号？',
                    style: TextStyle(
                      color: Colors.grey.withValues(alpha: 0.7),
                      fontSize: 14,
                    ),
                  ),
                  TextButton(
                    onPressed: _isRegistering ? null : () => Navigator.pop(context),
                    child: const Text(
                      '返回登录',
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