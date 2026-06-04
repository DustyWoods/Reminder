
import 'package:flutter/material.dart';
import 'package:reminder/Constants/main.dart';

class SelectorBar extends StatefulWidget {
  final double width;
  final double height;
  final calendarView currentOption;
  final Function(String year, String month, String day, calendarView) onChange;
  
  const SelectorBar({super.key,
    required this.width, 
    required this.height, 
    required this.currentOption, 
    required this.onChange,
  });
  
  @override
  State<SelectorBar> createState() => _SelectorBarState();
}

class _SelectorBarState extends State<SelectorBar> {

  int _getSelectedIndex() {
    switch(widget.currentOption) {
      case calendarView.year:
        return 0;
      case calendarView.month:
        return 1;
      case calendarView.day:
        return 2;
      case calendarView.schedule:
        return 3;
      default:
        return 0;
    }
  }

  void _handleTap(String text) {
    calendarView targetView;
    String year = DateTime.now().year.toString();
    String month = '';
    String day = '';
    
    switch(text) {
      case '年':
        targetView = calendarView.year;
        break;
      case '月':
        targetView = calendarView.month;
        month = DateTime.now().month.toString();
        break;
      case '日':
        targetView = calendarView.day;
        month = DateTime.now().month.toString();
        day = DateTime.now().day.toString();
        break;
      case '日程':
        targetView = calendarView.schedule;
        break;
      default:
        targetView = calendarView.year;
    }
    
    widget.onChange(year, month, day, targetView);
  }

  Widget _buildButtonPotion(calendarView viewOption, double selectorHeight) {
    String text = '';
    switch(viewOption) {
      case calendarView.year:
        text = '年';
        break;
      case calendarView.month:
        text = '月';
        break;
      case calendarView.day:
        text = '日';
        break;
      case calendarView.schedule:
        text = '日程';
        break;
      default:
        text = '年';
        break;
    }
    return Expanded(
      child: GestureDetector(
        onTap: () => _handleTap(text),
        child: Container(
          height: selectorHeight,
          alignment: Alignment.center,
          child: Text(
            text,
            style: TextStyle(
              color: widget.currentOption == viewOption ? Colors.black : Colors.grey[600],
              fontSize: 16,
              fontWeight: widget.currentOption == viewOption ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final selectorWidth = widget.width - 40;
    final selectorHeight = widget.height - 20;
    final buttonWidth = selectorWidth / 4;
    final selectedIndex = _getSelectedIndex();
    
    return Container(
      width: widget.width,
      height: widget.height,
      padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      color: Colors.transparent,
      child: Container(
        decoration: BoxDecoration(
          color: const Color.fromARGB(255, 105, 134, 197).withValues(alpha: 0.4),
          borderRadius: BorderRadius.circular(selectorHeight / 2),
          border: Border.all(
            color: Colors.grey.withValues(alpha: 0.8),
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.grey.withValues(alpha: 0.5),
              spreadRadius: 3,
              blurRadius: 7,
              offset: Offset(0, 2),
            ),
          ],
        ),
        width: selectorWidth,
        height: selectorHeight,
        child : Stack(
          children: [
            AnimatedPositioned(
              duration: Duration(milliseconds: 300),
              curve: Curves.easeInOut,
              left: selectedIndex * buttonWidth - 2,
              top : -2,
              width: buttonWidth,
              height: selectorHeight,
              child: Container(
                margin: EdgeInsets.symmetric(horizontal: 1.5, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular((selectorHeight) / 2 - 3),
                  border: Border.all(
                    color: Colors.transparent,
                    width: 2,
                  ),
                ),
              ),
            ),
            Row(
              children: [
                _buildButtonPotion(calendarView.year, selectorHeight),
                _buildButtonPotion(calendarView.month, selectorHeight),
                _buildButtonPotion(calendarView.day, selectorHeight),
                _buildButtonPotion(calendarView.schedule, selectorHeight),
              ],
            ),
          ],
        )
      ),
    );
  }
}
