import 'package:flutter/material.dart';
import 'package:reminder/Components/HomePage/Greet.dart';
import 'package:reminder/Components/HomePage/TaskBar.dart';
import 'package:reminder/Components/HomePage/VoiceInput.dart';
import 'package:reminder/Components/HomePage/VoiceMask.dart';
import 'package:reminder/Components/HomePage/Handling.dart';
import 'package:reminder/Components/HomePage/SwitchButton.dart';
import 'package:reminder/Components/HomePage/TextInput.dart';
import 'package:reminder/Components/HomePage/LoginButton.dart';
import 'package:reminder/Components/HomePage/HeadBar.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/Stores/TaskManager.dart';
import 'package:reminder/Stores/LoginManager.dart';
import 'package:reminder/Viewmodels/task.dart';

/// 主页面组件
/// 
/// 负责管理整个应用的主界面状态，包括：
/// - 登录状态检查
/// - 任务列表显示
/// - 语音/文本输入切换
/// - 语音输入处理流程
class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  
  // 是否正在语音输入中
  bool _onVoiceInputing = false;
  
  // 是否正在处理任务
  bool _isHandling = false;
  
  // 是否已初始化
  bool _isInitialized = false;
  
  // 是否已登录
  bool _isLoggedIn = false;
  
  // 当前输入模式：语音输入 / 文本输入
  bool _inputFlag = GlobalConstants.TEXT_INPUT;
  
  // 任务列表
  List<Task> _tasks = [];

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  /// 初始化应用
  Future<void> _initializeApp() async {
    // 初始化登录管理器
    await loginManager.init();
    
    // 检查登录状态
    _isLoggedIn = loginManager.isLoggedIn();
    
    // 如果已登录，初始化任务管理器
    if (_isLoggedIn) {
      await taskManager.init();
      _tasks = taskManager.getTasks();
    }
    
    if (mounted) {
      setState(() => _isInitialized = true);
    }
  }

  /// 登录成功回调
  void _onLoginSuccess() {
    setState(() {
      _isLoggedIn = true;
      _isInitialized = false;
    });
    
    _initializeApp();
  }

  /// 退出登录成功回调
  void _onLogoutSuccess() {
    setState(() {
      _isLoggedIn = false;
      _tasks = [];
    });
  }

  

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // 阻止键盘弹出时自动调整布局
      resizeToAvoidBottomInset: false,
      body: SafeArea(
        child: _buildBody(context),
      )
    );
  }

  /// 构建页面主体
  Widget _buildBody(BuildContext context) {
    // 未初始化时显示加载动画
    if (!_isInitialized) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }
    
    // 未登录时显示登录按钮
    if (!_isLoggedIn) {
      return Container(
        color: Colors.white,
        child: LoginButton(onLoginSuccess: _onLoginSuccess),
      );
    }
    
    // 已登录时显示主界面
    return Stack(
      children: [
        // 主内容区域（固定高度，不随键盘移动）
        SizedBox(
          height: ScreenSize.getHeight(context) - 80,
          child: Container(
            color: Colors.white,
            alignment: Alignment.center,
            child: Column(
              children: [
                SizedBox(
                  height: 50,
                  child: HeadBar(onLogoutSuccess: _onLogoutSuccess),
                ),
                // 问候语区域
                SizedBox(
                  height: ScreenSize.getHeight(context) * 0.15,
                  child: Greet(),
                ),
                // 任务列表区域
                SizedBox(
                  height : ScreenSize.getHeight(context) * 0.65,
                  child: 
                    _isInitialized ? 
                      TaskBar(tasks: _tasks, onDelete: _handleDelete)
                      : 
                      const Center(child: CircularProgressIndicator()),
                ),
              ],
            ),
          ),
        ),
        _onVoiceInputing ? VoiceMask() : Container(),
        
        // 输入模式
        _inputFlag == GlobalConstants.VOICE_INPUT ?
          VoiceInput(
            onVoiceInputBegin: _onVoiceInputBegin,
            onVoiceInputEnd: _onVoiceInputEnd,
          ) :
          TextInput(
            onSendSuccess: _onTextSendSuccess,
            onSendError: _onTextSendError,
          ),
        
        // 语音/文本输入切换按钮
        SwitchButton(flag: _inputFlag, onTap: _onInputModeSwitch),
        
        // 任务处理中的加载遮罩
        _isHandling ? Handling() : Container(),
      ],
    );
  }

  // ============== 语音输入回调处理 ==============

  /// 语音输入开始
  void _onVoiceInputBegin() {
    setState(() => _onVoiceInputing = true);
  }

  /// 语音输入结束，处理后端返回的结果
  /// 
  /// 后端返回的数据结构：
  /// {
  ///   "session_id": "xxx",
  ///   "text": "识别文本",
  ///   "is_final": true,
  ///   "task": {
  ///     "title": "任务标题",
  ///     "due_date": "2024-01-01 10:00",
  ///     "description": "任务描述"
  ///   },
  ///   "error": null  // 如果有错误
  /// }
  void _onVoiceInputEnd(Map<String, dynamic> result) {
    setState(() => _onVoiceInputing = false);
    
    // 优先使用后端返回的任务数据
    if (result.containsKey('task') && result['task'] != null) {
      print(result);
      _handleTaskResult(result['task']);
      return;
    }
    
    // 如果有识别文本但没有任务数据，显示错误
    if (result.containsKey('text') && 
        result['text'] != null && 
        result['text'].toString().isNotEmpty &&
        result.containsKey('error')) {
      print('语音识别完成，但任务处理失败: ${result['error']}');
    }
  }

  // ============== 任务处理 ==============

  /// 处理后端返回的任务结果
  void _handleTaskResult(Map<String, dynamic> taskData) {
    setState(() => _isHandling = true);
    
    try {
      // 解析截止日期
      final dueDateStr = taskData['due_date'] ?? '';
      final parts = dueDateStr.split(' ');
      final Map<String, String> dueDate = {
        'date': parts.isNotEmpty ? parts[0] : '',
        'time': parts.length > 1 ? parts[1] : '',
      };
      
      // 创建任务对象
      final task = Task(
        taskData['title'] ?? '新任务',
        taskData['description'] ?? '',
        dueDate,
      );
      
      // 保存任务
      taskManager.addTask(task).then((_) {
        setState(() {
          _tasks = taskManager.getTasks();
          _isHandling = false;
        });
      }).catchError((error) {
        print('Error saving task: $error');
        setState(() => _isHandling = false);
      });
    } catch (error) {
      print('Error processing task result: $error');
      setState(() => _isHandling = false);
    }
  }

  /// 文本发送成功回调
  void _onTextSendSuccess(Map<String, dynamic> result) {
    // 优先使用后端返回的任务数据
    if (result.containsKey('task') && result['task'] != null) {
      print(result);
      _handleTaskResult(result['task']);
      return;
    }
    
    // 如果有错误
    if (result.containsKey('error')) {
      print('文本发送完成，但任务处理失败: ${result['error']}');
    }
  }

  /// 文本发送失败回调
  void _onTextSendError(String error) {
    print('文本发送失败: $error');
  }

  /// 删除任务
  void _handleDelete(int index) {
    taskManager.removeTask(index).then((_) {
      setState(() {
        _tasks = taskManager.getTasks();
      });
    });
  }

  /// 切换输入模式
  void _onInputModeSwitch() {
    setState(() => _inputFlag = !_inputFlag);
  }
}