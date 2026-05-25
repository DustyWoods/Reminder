
import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class TextInput extends StatefulWidget {
  const TextInput({super.key});

  @override
  State<TextInput> createState() => _TextInputState();
}

class _TextInputState extends State<TextInput> {
  @override
  Widget build(BuildContext context) {
    return Positioned(
      bottom: 20,
      height: 60,
      width: ScreenSize.getWidth(context) * 0.8,
      right: ScreenSize.getWidth(context) * 0.1,
      child: Container(
        color: Colors.transparent,
        alignment: Alignment.center,
        child: GestureDetector(
          child: Container(
            width: ScreenSize.getWidth(context) * 0.8,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(30),
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withValues(alpha: 0.2),
                  blurRadius: 20,
                  offset: const Offset(0, 4),
                ),
              ],
              border: Border.all(
                color: Colors.grey.withValues(alpha: 0.2),
                width: 1,
              ),
            ),
            child: Icon(
              Icons.keyboard,
              size: 36,
              color: Colors.grey.withValues(alpha: 0.5),
            ),
          ),
        ),
      ),
    );

  }
}