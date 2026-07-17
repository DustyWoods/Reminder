
import 'package:flutter/material.dart';
import 'package:reminder/Components/CalendarPage/Label.dart';
import 'package:reminder/Components/CalendarPage/SelectorBar.dart';
import 'package:reminder/Constants/main.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/Components/CalendarPage/ScheduleView.dart';
import 'package:reminder/Components/CalendarPage/ScheduleLogo.dart';

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

    Widget _getView() {
      // if (currentView == calendarView.year) {
      //   return YearView(year: year, onDaySelected: _changeView);
      // } else if (currentView == calendarView.month) {
      //   return MonthView(year: year, month: month, onDaySelected: _changeView);
      // } else if (currentView == calendarView.day) {
      //   return DayView(year: year, month: month, day: day, onDaySelected: _changeView);
      // }
      return ScheduleView();
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('日程'),
        backgroundColor: const Color.fromARGB(255, 47, 98, 209),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SafeArea(
        child: Container(
          color: Colors.white,
          child: Column(
            children: [
              // Label(height: screenHeight * 0.08, year: year, month: month, day: day),
              // SelectorBar(width: ScreenSize.getWidth(context), height: screenHeight * 0.06, currentOption: currentView, onChange: _changeView),
              ScheduleLogo(height: screenHeight * 0.14),
              Container(
                height: screenHeight * 0.65,
                width: ScreenSize.getWidth(context),
                margin: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color.fromARGB(255, 142, 171, 235),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Container(
                  height: double.infinity,
                  width: double.infinity,
                  color: Colors.white,
                  child: _getView(),
                ),
              ),
            ],
          )
        )
      )
    );
  }
}

