import 'package:flutter/material.dart';
import 'package:reminder/Stores/LoginManager.dart';
import 'package:reminder/Components/RegisterPage/LogoSection.dart';
import 'package:reminder/Components/RegisterPage/TitleSection.dart';
import 'package:reminder/Components/RegisterPage/UsernameInput.dart';
import 'package:reminder/Components/RegisterPage/PasswordInput.dart';
import 'package:reminder/Components/RegisterPage/ConfirmPasswordInput.dart';
import 'package:reminder/Components/RegisterPage/RegisterButton.dart';
import 'package:reminder/Components/RegisterPage/LoginLink.dart';

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
              const LogoSection(),
              
              const SizedBox(height: 20),
              
              // 标题
              const TitleSection(),
              
              const SizedBox(height: 30),
              
              // 用户名输入框
              UsernameInput(
                controller: _usernameController,
                focusNode: _usernameFocus,
                enabled: !_isRegistering,
                nextFocusNode: _passwordFocus,
              ),
              
              const SizedBox(height: 20),
              
              // 密码输入框
              PasswordInput(
                controller: _passwordController,
                focusNode: _passwordFocus,
                enabled: !_isRegistering,
                nextFocusNode: _confirmPasswordFocus,
              ),
              
              const SizedBox(height: 20),
              
              // 确认密码输入框
              ConfirmPasswordInput(
                controller: _confirmPasswordController,
                focusNode: _confirmPasswordFocus,
                enabled: !_isRegistering,
                onSubmitted: _handleRegister,
              ),
              
              const SizedBox(height: 40),
              
              // 注册按钮
              RegisterButton(
                isLoading: _isRegistering,
                onPressed: _handleRegister,
              ),
              
              const SizedBox(height: 20),
              
              // 返回登录提示
              LoginLink(
                enabled: !_isRegistering,
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
        ),
      ),
    );
  }
}