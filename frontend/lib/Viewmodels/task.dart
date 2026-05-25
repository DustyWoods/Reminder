
class Task {
  String title;
  String description;
  Map<String, String> dueDate;
  bool isCompleted = false;

  Task(this.title, this.description, this.dueDate);

  Task.fromJson(Map<String, dynamic> json)
      : title = json['title'] ?? '',
        description = json['description'] ?? '',
        dueDate = (json['dueDate'] as Map<String, dynamic>?)?.map(
          (key, value) => MapEntry(key, value?.toString() ?? ''),
        ) ?? {'date': '', 'time': ''},
        isCompleted = json['isCompleted'] ?? false;
}