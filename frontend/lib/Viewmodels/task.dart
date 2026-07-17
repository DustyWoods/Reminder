
class Task {
  String title;
  String description;
  Map<String, String> dueDate;
  bool isCompleted = false;
  int? id;

  Task(this.title, this.description, this.dueDate, {this.id});

  Task.fromJson(Map<String, dynamic> json)
      : title = json['title'] ?? '',
        description = json['description'] ?? '',
        dueDate = _parseDueDate(json),
        isCompleted = json['isCompleted'] ?? json['completed'] ?? false,
        id = json['id'] as int?;

  static Map<String, String> _parseDueDate(Map<String, dynamic> json) {
    // 支持两种格式：
    // 1. 后端返回的字符串格式: "due_date": "2026-06-30 18:00"
    // 2. 前端本地存储的 Map 格式: "dueDate": {"date": "2026-06-30", "time": "18:00"}
    if (json.containsKey('due_date') && json['due_date'] is String) {
      String dateStr = json['due_date'];
      if (dateStr.contains(' ')) {
        List<String> parts = dateStr.split(' ');
        return {'date': parts[0], 'time': parts.length > 1 ? parts[1] : ''};
      }
      return {'date': dateStr, 'time': ''};
    } else if (json.containsKey('dueDate') && json['dueDate'] is Map) {
      return (json['dueDate'] as Map<String, dynamic>).map(
        (key, value) => MapEntry(key, value?.toString() ?? ''),
      );
    }
    return {'date': '', 'time': ''};
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'description': description,
      'dueDate': dueDate,
      'isCompleted': isCompleted,
      'id': id,
    };
  }

  bool isDailyTask() {
    final time = dueDate['time'] ?? '';
    return time.isEmpty || time == '23:59';
  }

  bool isExpired() {
    final dateStr = dueDate['date'] ?? '';
    if (dateStr.isEmpty) return false;
    
    final today = DateTime.now();
    final dateParts = dateStr.split('-');
    if (dateParts.length != 3) return false;
    
    try {
      final year = int.parse(dateParts[0]);
      final month = int.parse(dateParts[1]);
      final day = int.parse(dateParts[2]);
      final taskDate = DateTime(year, month, day);
      
      final timeStr = dueDate['time'] ?? '';
      if (timeStr.isEmpty) {
        return taskDate.isBefore(today);
      }
      
      final timeParts = timeStr.split(':');
      if (timeParts.length != 2) return taskDate.isBefore(today);
      
      final hour = int.parse(timeParts[0]);
      final minute = int.parse(timeParts[1]);
      final taskDateTime = DateTime(year, month, day, hour, minute);
      
      return taskDateTime.isBefore(today);
    } catch (_) {
      return false;
    }
  }
}