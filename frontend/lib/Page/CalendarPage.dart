
import 'package:flutter/material.dart';
import 'package:reminder/Components/CalendarPage/Label.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class CalendarPage extends StatefulWidget {
  const CalendarPage({super.key});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  @override
  Widget build(BuildContext context) {
    final screenHeight = ScreenSize.getHeight(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('时日清单'),
        backgroundColor: const Color.fromARGB(255, 47, 98, 209),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SafeArea(
        child: Container(
          color: Colors.white,
          child: Column(
            children: [
              SizedBox(
                height: screenHeight * 0.08,
                child: Label(height: screenHeight * 0.08, year: '2023', month: '08', day: '01'),
              ),
            ],
          )
        )
      )
    );
  }
}
