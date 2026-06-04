
import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';
import 'package:reminder/constants/main.dart';

class SwitchButton extends StatelessWidget {
  final bool flag;
  final Function() onTap;

  const SwitchButton({super.key, required this.flag, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      bottom: ScreenSize.getBottomInset(context) + 20,
      height: 60,
      width: 60,
      left: ScreenSize.getWidth(context) * 0.1,
      child: Container(
        color: Colors.transparent,
        alignment: Alignment.centerLeft,
        padding: const EdgeInsets.only(left: 5),
        child: GestureDetector(
          onTap: onTap,
          child: Container(
            height: 50,
            width: 50,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: flag == HomePageConstants.VOICE_INPUT ? Colors.white: const Color.fromARGB(255, 47, 98, 209),
              borderRadius: BorderRadius.circular(25),
            ),
            child: Icon(
              flag == HomePageConstants.VOICE_INPUT ? Icons.keyboard: Icons.mic,
              size: 28,
              color: flag == HomePageConstants.VOICE_INPUT ? Colors.grey: Colors.white,
            ),
          ),
        ),
      ),
    );

  }
}