import 'package:flutter/material.dart';

class ScheduleLogo extends StatefulWidget {
  final double height;
  const ScheduleLogo({super.key, required this.height});

  @override
  State<ScheduleLogo> createState() => _ScheduleLogoState();
}

class _ScheduleLogoState extends State<ScheduleLogo> {

  @override
  Widget build(BuildContext context) {
    return Container(
      height: widget.height,
      color: Colors.transparent,
      padding: EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          Container(
            height: widget.height * 0.5,
            width: widget.height * 0.5,
            decoration: BoxDecoration(
              color: const Color.fromARGB(255, 105, 134, 197),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: Colors.grey,
                width: 2,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withValues(alpha: 0.5),
                  spreadRadius: 2,
                  blurRadius: 4,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: Icon(
              Icons.event_note,
              size: widget.height * 0.4,
              color: Colors.white,
            ),
          ),
          SizedBox(width: 15),
          Text(
            '任务列表',
            style: TextStyle(
              color: const Color.fromARGB(255, 105, 134, 197),
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          )
        ]
      )
    );
  }
}