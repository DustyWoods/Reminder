
import 'package:flutter/material.dart';
import 'package:collection/collection.dart';
import 'package:reminder/Viewmodels/task.dart';
import 'package:reminder/Stores/TaskManager.dart';
import 'package:reminder/Components/HomePage/TaskCard.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class ScheduleView extends StatefulWidget {
  const ScheduleView({super.key});

  @override
  State<ScheduleView> createState() => _ScheduleViewState();
}

class _ScheduleViewState extends State<ScheduleView> {
  List<Task> tasks = [];

  @override
  void initState() {
    super.initState();
    tasks = taskManager.getTasks();
  }

  Future<void> _onDeleteTask(int taskId) async {
    await taskManager.removeTaskById(taskId);
    if (!mounted) return;
    setState(() {
      tasks = taskManager.getTasks();
    });
  }

  @override
  Widget build(BuildContext context) {
    final Map<String, List<Task>> tasksMap = groupBy(tasks, (task) => task.dueDate['date'] ?? '');
    final List<List<Task>> tasksByDate = (tasksMap.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key)))
      .map((entry) {
        entry.value.sort((a, b) {
          final timeA = a.dueDate['time'] ?? '';
          final timeB = b.dueDate['time'] ?? '';
          if (timeA.isEmpty) return 1;
          if (timeB.isEmpty) return -1;
          return timeA.compareTo(timeB);
        });
        return entry.value;
      })
      .toList();

    if (tasksByDate.isEmpty) {
      return Center(
        child: Text(
          '暂无日程安排',
          style: TextStyle(
            fontSize: 24,
            color: const Color.fromARGB(255, 86, 127, 216),
            fontWeight: FontWeight.bold,
          ),
        ),
      );
    }

    return ListView.builder(
      itemCount: tasksByDate.length,
      itemBuilder: (context, index) {
        return Container(
          color: Colors.transparent,
          padding: EdgeInsets.all(10),
          margin: EdgeInsets.all(5),
          child: Column(
            children: [
              SizedBox(
                width: double.infinity,
                child: Text(
                  '${tasksByDate[index].first.dueDate['date']}',
                  textAlign: TextAlign.left,
                  style: TextStyle(
                    fontSize: 20, 
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic,
                    ),
                ),
              ),
              ...tasksByDate[index].map((task) => SizedBox(
                height: ScreenSize.getHeight(context) * 0.12,
                child: TaskCard(
                  key: Key('task_${task.id}_${task.title}'),
                  task: task,
                  onDelete: () => _onDeleteTask(task.id ?? -1),
                ),
              )),
            ],
          ),
        );
      },
    );
  }
}
