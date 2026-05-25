
import 'package:flutter/material.dart';
import 'package:reminder/Utils/ScreenSize.dart';
class VoiceText extends StatefulWidget {
  final String text;
  const VoiceText({super.key, required this.text});

  @override
  State<VoiceText> createState() => _VoiceTextState();
}

class _VoiceTextState extends State<VoiceText> {
  final ScrollController _scrollController = ScrollController();

  @override
  void didUpdateWidget(VoiceText oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.text != widget.text) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

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
        color: Colors.grey.withValues(alpha: 0.3),
        child: Container(
          height: ScreenSize.getHeight(context) * 0.25,
          width: double.infinity,
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          margin: EdgeInsets.symmetric(horizontal: 20),
          decoration: BoxDecoration(
            color: const Color.fromARGB(255, 166, 186, 228).withValues(alpha: 0.8),
            borderRadius: BorderRadius.circular(10),
          ),
          alignment: Alignment.center,
          child: SingleChildScrollView(
            controller: _scrollController,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Text(
                widget.text,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.black,
                ),
              ),
            ),
          ),
        ),
      )
    );
  }
}