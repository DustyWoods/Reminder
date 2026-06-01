
import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class HeadBar extends StatelessWidget {
  const HeadBar({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: ScreenSize.getWidth(context),
      decoration: BoxDecoration(
        color: Colors.transparent,
        border: Border(
          bottom: BorderSide(
            color: const Color.fromARGB(255, 18, 53, 131).withValues(alpha: 0.5),
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Container(
            margin: const EdgeInsets.only(left: 20),
            child: const Icon(
              Icons.calendar_month,
              color: Color.fromARGB(255, 29, 99, 204),
              size: 40
            ),
          ),
          Container(
            margin: const EdgeInsets.only(right: 20),
            child: const Icon(
              Icons.account_circle,
              color: Color.fromARGB(255, 2, 69, 170),
              size: 40
            ),
          ),
        ],
      ),
    );
  }
}