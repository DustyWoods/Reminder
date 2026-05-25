
import 'package:flutter/material.dart';
import 'package:reminder/Components/HomePage/Greet.dart';
import 'package:reminder/Components/HomePage/TaskBar.dart';
import 'package:reminder/Components/HomePage/VoiceInput.dart';
import 'package:reminder/Components/HomePage/VoiceText.dart';
import 'package:reminder/Components/HomePage/Handling.dart';
import 'package:reminder/Components/HomePage/SwitchButton.dart';
import 'package:reminder/Components/HomePage/TextInput.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/api/TextService.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/stores/TokenManager.dart';
import 'package:reminder/Viewmodels/task.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _recognizedText = "";
  bool _onVoiceInputing = false;
  bool _isHandling = false;
  bool _isInitialized = false;
  bool _inputFlag = GlobalConstants.VOICE_INPUT;
  List<Task> _tasks = [];

  @override
  void initState() {
    super.initState();
    _initializeTokenManager();
  }

  Future<void> _initializeTokenManager() async {
    await tokenManager.init();
    _tasks = tokenManager.getTasks();
    if (mounted) {
      setState(() => _isInitialized = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Stack(
          children: [
            Container(
              color: Colors.white,
              alignment: Alignment.center,
              child: Column(
                children: [
                  SizedBox(
                    height: ScreenSize.getHeight(context) * 0.15,
                    child: Greet(),
                  ),
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
            _onVoiceInputing ? VoiceText(text: _recognizedText) : Container(),
            _inputFlag == GlobalConstants.VOICE_INPUT ? 
              VoiceInput(
                onSet: onSet, 
                onClean: onClean, 
                onVoiceInputBegin: voiceInputBegin, 
                onVoiceInputEnd: voiceInputEnd)
                :
                TextInput(),
            SwitchButton(flag: _inputFlag, onTap: onSwitch),
            _isHandling ? Handling() : Container(),
          ],
        ),
      )
    );
  }

  void onClean() {
    setState(() => _recognizedText = "");
  }

  void onSet(String text) {
    setState(() => _recognizedText = text);
  }

  void voiceInputBegin() {
    setState(() => _onVoiceInputing = true);
  }

  void voiceInputEnd() {
    setState(() => _onVoiceInputing = false);
    onHandle();
    // if (_recognizedText.isNotEmpty) {
    //   onHandle();
    // }
  }

  void onHandle() {
    setState(() => _isHandling = true);
    TextService.getTask(_recognizedText).then((value) {
      print('API response: $value');
      if (value == null || value.isEmpty) {
        throw Exception('Empty response');
      }
      final dueDateStr = value['due_date'] ?? '';
      final parts = dueDateStr.split(' ');
      final Map<String, String> dueDate = {
        'date': parts.isNotEmpty ? parts[0] : '',
        'time': parts.length > 1 ? parts[1] : '',
      };
      final task = Task(
        value['title'] ?? '新任务',
        value['description'] ?? '',
        dueDate,
      );
      tokenManager.addTask(task).then((_) {
        setState(() {
          _tasks = tokenManager.getTasks();
          _isHandling = false;
        });
      });
    }).catchError((error) {
      print('Error creating task: $error');
      setState(() => _isHandling = false);
    });
  }

  void _handleDelete(int index) {
    tokenManager.removeTask(index).then((_) {
      setState(() {
        _tasks = tokenManager.getTasks();
      });
    });
  }

  void onSwitch() {
    setState(() => _inputFlag = !_inputFlag);
  }
}