import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:reminder/Components/HomePage/MainContent.dart';
import 'package:reminder/Components/HomePage/LoadingView.dart';
import 'package:reminder/Components/HomePage/UnauthenticatedView.dart';
import 'package:reminder/Components/HomePage/VoiceInput.dart';
import 'package:reminder/Components/HomePage/VoiceMask.dart';
import 'package:reminder/Components/HomePage/SwitchButton.dart';
import 'package:reminder/Components/HomePage/TextInput.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Stores/TaskManager.dart';
import 'package:reminder/Stores/LoginManager.dart';
import 'package:reminder/Viewmodels/task.dart';
import 'package:reminder/Services/NotificationService.dart';

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
  
  // 是否已初始化
  bool _isInitialized = false;
  
  // 是否已登录
  bool _isLoggedIn = false;
  
  // 当前输入模式：语音输入 / 文本输入
  bool _inputFlag = HomePageConstants.TEXT_INPUT;
  
  // 今日任务列表（已筛选和排序）
  List<Task> _todayTasks = [];

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  /// 初始化应用
  Future<void> _initializeApp() async {
    print('Initialization started');
    
    try {
      print('Step 1: loginManager.init()');
      await loginManager.init();
      print('Step 1 done');
      
      print('Step 2: notificationService.init()');
      await notificationService.init();
      print('Step 2 done');
      
      print('Step 3: _requestNotificationPermission()');
      await _requestNotificationPermission();
      print('Step 3 done');
      
      print('Step 4: check login status');
      _isLoggedIn = loginManager.isLoggedIn();
      print('Login status: $_isLoggedIn');
      
      if (_isLoggedIn) {
        print('Step 5: taskManager.init()');
        await taskManager.init();
        print('Step 5 done');
        
        print('Step 6: getTodayTasks()');
        _todayTasks = taskManager.getTodayTasks();
        print('Today tasks count: ${_todayTasks.length}');
        
        print('Step 7: scheduleNotificationsForToday()');
        await notificationService.scheduleNotificationsForToday();
        print('Step 7 done');
      }
    } catch (e, stackTrace) {
      print('Initialization error: $e');
      print('Stack trace: $stackTrace');
    } finally {
      print('Setting _isInitialized = true');
      if (mounted) {
        setState(() => _isInitialized = true);
      }
      print('Initialization finished');
    }
  }

  /// 请求通知权限
  Future<void> _requestNotificationPermission() async {
    final status = await Permission.notification.request();
    if (status.isGranted) {
      print('Notification permission granted');
    } else {
      print('Notification permission denied');
    }
  }

  /// 登录成功回调
  void _onLoginSuccess() {
    taskManager.reset();
    setState(() {
      _isLoggedIn = true;
      _isInitialized = false;
    });
    
    _initializeApp();
  }

  /// 退出登录成功回调
  void _onLogoutSuccess() {
    taskManager.reset();
    setState(() {
      _isLoggedIn = false;
      _todayTasks = [];
    });
  }

  /// 从日历页面返回时刷新任务列表
  void _onCalendarBack() {
    setState(() {
      _todayTasks = taskManager.getTodayTasks();
    });
    notificationService.scheduleNotificationsForToday();
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
      return const LoadingView();
    }

    // 未登录时显示登录按钮
    if (!_isLoggedIn) {
      return UnauthenticatedView(onLoginSuccess: _onLoginSuccess);
    }

    // 已登录时显示主界面
    return Stack(
      children: [
        // 主内容区域
        MainContent(
          onLogoutSuccess: _onLogoutSuccess,
          isInitialized: _isInitialized,
          tasks: _todayTasks,
          onDeleteTask: _handleDeleteTask,
          onCalendarBack: _onCalendarBack,
        ),

        _onVoiceInputing ? const VoiceMask() : Container(),

        // 输入模式
        _inputFlag == HomePageConstants.VOICE_INPUT
          ? VoiceInput(
              onVoiceInputBegin: _onVoiceInputBegin,
              onVoiceInputEnd: _onVoiceInputEnd,
            )
          : TextInput(
              onSendSuccess: _onTextSendSuccess,
              onSendError: _onTextSendError,
            ),

        // 语音/文本输入切换按钮
        SwitchButton(flag: _inputFlag, onTap: _onInputModeSwitch),
      ],
    );
  }

  // ============== 语音输入回调处理 ==============

  /// 语音输入开始
  void _onVoiceInputBegin() {
    setState(() => _onVoiceInputing = true);
  }

  /// 语音输入结束，处理后端返回的结果
  void _onVoiceInputEnd(Map<String, dynamic> result) {
    setState(() => _onVoiceInputing = false);
    _handleServerResponse(result);
  }

  // ============== 任务处理 ==============

  /// 统一处理服务端响应（文本输入和语音输入共用）
  void _handleServerResponse(Map<String, dynamic> result) {
    final operation = result['operation'] ?? 'create';
    final success = result['success'] ?? false;
    final summary = result['summary'] ?? '';

    print('Operation: $operation, Success: $success, Summary: $summary');

    Future<void> updateUI() async {
      if (mounted) {
        setState(() => _todayTasks = taskManager.getTodayTasks());
      }
      await notificationService.scheduleNotificationsForToday();
    }

    final tasksData = result['tasks'];
    if (tasksData is List && tasksData.isNotEmpty) {
      if (operation == 'mixed') {
        taskManager.refreshTasks().then((_) => updateUI()).catchError((e) {
          print('Error refreshing tasks: $e');
          return null;
        });
      } else {
        taskManager.syncTasksFromServer(operation, tasksData).then((syncSuccess) {
          if (syncSuccess) updateUI();
        }).catchError((e) {
          print('Error syncing tasks: $e');
          return null;
        });
      }
    } else {
      if (success && (operation == 'delete' || operation == 'update' || operation == 'mixed')) {
        taskManager.refreshTasks().then((_) => updateUI()).catchError((e) {
          print('Error refreshing tasks: $e');
          return null;
        });
      }
    }
  }

  /// 文本发送成功回调
  void _onTextSendSuccess(Map<String, dynamic> result) {
    _handleServerResponse(result);
  }

  /// 文本发送失败回调
  void _onTextSendError(String error) {
    print('文本发送失败: $error');
  }

  /// 删除任务（根据任务ID）
  void _handleDeleteTask(int taskId) {
    taskManager.removeTaskById(taskId).then((_) {
      setState(() {
        _todayTasks = taskManager.getTodayTasks();
      });
      notificationService.scheduleNotificationsForToday();
    });
  }

  /// 切换输入模式
  void _onInputModeSwitch() {
    setState(() => _inputFlag = !_inputFlag);
  }
}