
import 'package:flutter/material.dart';

class VoiceText extends StatelessWidget {
  const VoiceText({super.key});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: 0,
      bottom: 0,
      left: 0,
      right: 0,
      child: Container(
        height: double.infinity,
        width: double.infinity,
        alignment: Alignment.center,
        color: Colors.grey.withValues(alpha: 0.5),
      )
    );
  }
}