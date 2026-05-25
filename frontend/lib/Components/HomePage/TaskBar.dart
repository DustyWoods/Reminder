
import 'package:flutter/material.dart';
import 'package:reminder/Viewmodels/task.dart';
import 'package:reminder/Components/HomePage/TaskCard.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class TaskBar extends StatelessWidget {
  final List<Task> tasks;
  final Function(int) onDelete;
  const TaskBar({super.key, required this.tasks, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    return 
      tasks.isEmpty ?
        Center(
          child: Text(
            '今日放个假~~',
						style: TextStyle(
							fontSize: 36, 
							color: const Color.fromARGB(255, 86, 127, 216),
							fontWeight: FontWeight.bold,
						),
          )
        )
        :
        ListView.builder(
          itemBuilder: (context, index) {
            return SizedBox(
              height: ScreenSize.getHeight(context) * 0.12,
              child :Row(
                children:[
                  Container(
                    width: 50,
                    padding: EdgeInsets.only(left: 15),
                    alignment: Alignment.center,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(
                          child: Container(
                            width: 5,
                            decoration: BoxDecoration(
                              color: index != 0 ? const Color.fromARGB(255, 107, 141, 216) : Colors.transparent,
                              borderRadius: BorderRadius.only(
                                bottomLeft: Radius.circular(2.5),
                                bottomRight: Radius.circular(2.5),
                              ),
                            ),
                          )
                        ),
                        SizedBox(height: 5,),
                        Icon(
                          Icons.circle,
                          size: 12,
                          color: const Color.fromARGB(255, 19, 80, 211),
                        ),
                        SizedBox(height: 5,),
                        Expanded(
                          child: Container(
                            width: 5,
                            decoration: BoxDecoration(
                              color: index != tasks.length - 1 ? const Color.fromARGB(255, 107, 141, 216) : Colors.transparent,
                              borderRadius: BorderRadius.only(
                                topLeft: Radius.circular(2.5),
                                topRight: Radius.circular(2.5),
                              ),
                            ),
                          ),
                        )
                      ]                 
                    )
                  ),
                  Expanded(
                    child: TaskCard(
                      key: Key(DateTime.now().millisecondsSinceEpoch.toString() + '_index'),
                      task: tasks[index], 
                      onDelete: () => onDelete(index),
                    ),
                  ),
                ],
              )
            );
          },
          itemCount: tasks.length,
        );
  }
}
