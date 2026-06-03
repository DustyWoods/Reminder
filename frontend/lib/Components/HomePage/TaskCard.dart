
import 'package:flutter/material.dart';
import 'package:reminder/Viewmodels/task.dart';
import 'package:reminder/Utils/ScreenSize.dart';

class TaskCard extends StatefulWidget {
  const TaskCard({super.key, required this.task, required this.onDelete});

  final Task task;
  final VoidCallback onDelete;

  @override
  State<TaskCard> createState() => _TaskCardState();
}

class _TaskCardState extends State<TaskCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _offsetAnimation;
  double _offsetX = 0;
  double _startX = 0;
  bool _isDragging = false;
  final double _deleteThreshold = 120;
  final double _maxOffset = 180;
  final double _resistanceFactor = 0.7;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 350),
    );
    _offsetAnimation = _controller.drive(Tween<double>(begin: 0, end: 0));
    _offsetAnimation.addListener(() {
      setState(() {
        _offsetX = _offsetAnimation.value;
      });
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant TaskCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.task.title != widget.task.title || 
        oldWidget.task.dueDate['time'] != widget.task.dueDate['time']) {
      _offsetX = 0;
      _controller.reset();
    }
  }

  void _onPanStart(DragStartDetails details) {
    _controller.stop();
    _startX = details.localPosition.dx;
    _isDragging = true;
  }

  void _onPanUpdate(DragUpdateDetails details) {
    if (!_isDragging) return;
    double delta = details.localPosition.dx - _startX;
    double resistance = 1.0;
    if (delta > _deleteThreshold) {
      resistance = _resistanceFactor + (1 - _resistanceFactor) * (_deleteThreshold / delta);
    }
    double newOffset = _offsetX + delta * resistance;
    setState(() {
      _offsetX = newOffset.clamp(0, _maxOffset);
    });
    _startX = details.localPosition.dx;
  }

  void _onPanEnd(DragEndDetails details) {
    _isDragging = false;
    
    if (_offsetX >= _deleteThreshold) {
      _animateToDelete();
    } else {
      _animateBack();
    }
  }

  void _animateBack() {
    final currentOffset = _offsetX;
    _controller.reset();
    _offsetAnimation = _controller.drive(
      Tween<double>(begin: currentOffset, end: 0).chain(
        CurveTween(curve: Curves.elasticOut),
      ),
    );
    _controller.forward();
  }

  void _animateToDelete() {
    final currentOffset = _offsetX;
    _controller.reset();
    final screenWidth = ScreenSize.getWidth(context);
    final cardWidth = screenWidth * 0.8;
    final endOffset = cardWidth + 100;
    _offsetAnimation = _controller.drive(
      Tween<double>(begin: currentOffset, end: endOffset).chain(
        CurveTween(curve: Curves.easeIn),
      ),
    );
    _controller.forward().then((_) {
      widget.onDelete();
    });
  }

  double get _opacity {
    return (1.0 - (_offsetX / _maxOffset) * 0.4).clamp(0.0, 1.0);
  }

  double get _scale {
    return (1.0 - (_offsetX / _maxOffset) * 0.05).clamp(0.9, 1.0);
  }

  double get _deleteIconOpacity {
    return (_offsetX / _deleteThreshold).clamp(0.0, 1.0);
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Positioned(
          left: 0,
          right: 0,
          top: 0,
          bottom: 0,
          child: AnimatedOpacity(
            opacity: _deleteIconOpacity,
            duration: const Duration(milliseconds: 150),
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.red,
                borderRadius: BorderRadius.circular(16),
              ),
              alignment: Alignment.centerLeft,
              padding: const EdgeInsets.only(left: 32),
              child: const Icon(
                Icons.delete,
                color: Colors.white,
                size: 28,
              ),
            ),
          ),
        ),
        GestureDetector(
          onPanStart: _onPanStart,
          onPanUpdate: _onPanUpdate,
          onPanEnd: _onPanEnd,
          child: Transform(
            transform: Matrix4.translationValues(_offsetX, 0, 0)
              ..scale(_scale, _scale),
            alignment: Alignment.center,
            child: AnimatedOpacity(
              opacity: _opacity,
              duration: const Duration(milliseconds: 150),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                height: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.grey.withValues(alpha: 0.1),
                      spreadRadius: 0,
                      blurRadius: 10,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(
                      widget.task.title,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.black,
                      ),
                    ),
                    Text(
                      widget.task.dueDate['time'] ?? '',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey[1000],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}