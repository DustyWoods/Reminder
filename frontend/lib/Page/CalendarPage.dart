
import 'package:flutter/material.dart';
import 'package:reminder/Components/CalendarPage/Label.dart';
import 'package:reminder/Components/CalendarPage/SelectorBar.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class CalendarPage extends StatefulWidget {
  const CalendarPage({super.key});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  String year = DateTime.now().year.toString();
  String month = '';
  String day = '';

  calendarView currentView = calendarView.year;

  void _changeView(String newYear, String newMonth, String newDay, calendarView view) {
    setState(() {
      year = newYear;
      month = newMonth;
      day = newDay;
      currentView = view;
    });
  }

  @override
  Widget build(BuildContext context) {
    final screenHeight = ScreenSize.getHeight(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('任务清单'),
        backgroundColor: const Color.fromARGB(255, 47, 98, 209),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SafeArea(
        child: Container(
          color: Colors.white,
          child: Column(
            children: [
              Label(height: screenHeight * 0.08, year: year, month: month, day: day),
              SelectorBar(width: ScreenSize.getWidth(context), height: screenHeight * 0.06, currentOption: currentView, onChange: _changeView),
            ],
          )
        )
      )
    );
  }
}
