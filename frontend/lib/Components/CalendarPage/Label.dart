
import 'package:flutter/material.dart';

class Label extends StatefulWidget {
  final double height;
  final String year;
  final String month;
  final String day;
  const Label({super.key, required this.height, required this.year, required this.month, required this.day});

  @override
  State<Label> createState() => _LabelState();
}

class _LabelState extends State<Label> {

  Widget _buildText(String text, {bool flag = false}) {
    return Text.rich(
      TextSpan(
        text: flag ? '/' : '',
        style: TextStyle(
          color: Colors.black,
          fontSize: 32,
          fontWeight: FontWeight.bold,
        ),
        children: [
          TextSpan(
            text: text,
            style: TextStyle(
              color: const Color.fromARGB(255, 105, 134, 197),
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      )
    );
  }

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
            height: widget.height * 0.7,
            width: widget.height * 0.7,
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
              size: widget.height * 0.6,
              color: Colors.white,
            ),
          ),
          SizedBox(width: 15),
          _buildText(widget.year),
          widget.month.isNotEmpty ? _buildText(widget.month, flag: true) : Container(),
          widget.day.isNotEmpty ? _buildText(widget.day, flag: true) : Container(),
        ]
      )
    );
  }
}