import 'package:flutter/material.dart';
import 'package:reminder/Components/HomePage/MainContent.dart';
import 'package:reminder/Components/HomePage/LoadingView.dart';
import 'package:reminder/Components/HomePage/UnauthenticatedView.dart';
import 'package:reminder/Components/HomePage/VoiceInput.dart';
import 'package:reminder/Components/HomePage/VoiceMask.dart';
import 'package:reminder/Components/HomePage/Handling.dart';
import 'package:reminder/Components/HomePage/SwitchButton.dart';
import 'package:reminder/Components/HomePage/TextInput.dart';
import 'package:reminder/Constants/main.dart';
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
  bool _inputFlag = HomePageConstants.TEXT_INPUT;
  
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
          tasks: _tasks,
          onDelete: _handleDelete,
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

        // 任务处理中的加载遮罩
        _isHandling ? const Handling() : Container(),
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
  ///   "tasks": [
  ///     {
  ///       "title": "任务标题1",
  ///       "due_date": "2024-01-01 10:00",
  ///       "description": "任务描述1"
  ///     },
  ///     {
  ///       "title": "任务标题2",
  ///       "due_date": "2024-01-02 14:00",
  ///       "description": "任务描述2"
  ///     }
  ///   ],
  ///   "error": null  // 如果有错误
  /// }
  void _onVoiceInputEnd(Map<String, dynamic> result) {
    setState(() => _onVoiceInputing = false);
    
    // 优先使用后端返回的多任务数据
    if (result.containsKey('tasks') && result['tasks'] != null) {
      final tasksData = result['tasks'];
      if (tasksData is List) {
        print('Received ${tasksData.length} task(s) from voice input');
        for (var taskData in tasksData) {
          _handleTaskResult(taskData);
        }
        return;
      }
    }
    
    // 兼容旧版单任务格式
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
  /// 
  /// 后端 ReAct Agent 返回的统一格式：
  /// {
  ///   "operation": "create/update/delete/query/mixed",
  ///   "operations": ["create", "delete"],
  ///   "success": true/false,
  ///   "summary": "操作结果总结",
  ///   "message": "操作结果消息",
  ///   "tasks": [...],
  ///   "results": [...],
  ///   "plan": [...]
  /// }
  void _onTextSendSuccess(Map<String, dynamic> result) {
    // 获取操作类型
    final operation = result['operation'] ?? 'create';
    final success = result['success'] ?? false;
    final summary = result['summary'] ?? result['message'] ?? '';
    
    print('Operation: $operation, Success: $success, Summary: $summary');
    
    // 获取任务列表
    final tasksData = result['tasks'];
    if (tasksData is List && tasksData.isNotEmpty) {
      // 处理混合操作：逐个处理结果中的任务
      if (operation == 'mixed') {
        taskManager.refreshTasks().then((_) {
          setState(() {
            _tasks = taskManager.getTasks();
          });
        }).catchError((error) {
          print('Error refreshing tasks: $error');
        });
      } else {
        // 单一操作类型
        taskManager.syncTasksFromServer(operation, tasksData).then((syncSuccess) {
          if (syncSuccess) {
            setState(() {
              _tasks = taskManager.getTasks();
            });
            print('Local tasks synchronized successfully');
          }
        }).catchError((error) {
          print('Error syncing tasks: $error');
        });
      }
    } else {
      // 如果没有任务数据但操作成功（如删除操作），刷新本地数据
      if (success && (operation == 'delete' || operation == 'update' || operation == 'mixed')) {
        taskManager.refreshTasks().then((_) {
          setState(() {
            _tasks = taskManager.getTasks();
          });
        });
      }
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