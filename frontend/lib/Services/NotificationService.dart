import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:reminder/Viewmodels/task.dart';
import 'package:reminder/Stores/TaskManager.dart';
import 'package:intl/intl.dart';
import 'package:timezone/data/latest_all.dart';
import 'package:timezone/timezone.dart' as tz;

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  late FlutterLocalNotificationsPlugin _flutterLocalNotificationsPlugin;
  bool _isInitialized = false;

  Future<void> init() async {
    if (_isInitialized) return;

    initializeTimeZones();

    _flutterLocalNotificationsPlugin = FlutterLocalNotificationsPlugin();

    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const InitializationSettings initializationSettings =
        InitializationSettings(
      android: initializationSettingsAndroid,
    );

    await _flutterLocalNotificationsPlugin.initialize(
      settings: initializationSettings,
    );

    const AndroidNotificationChannel channel = AndroidNotificationChannel(
      'reminder_channel',
      '任务提醒',
      description: '任务截止时间提醒',
      importance: Importance.high,
    );

    await _flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);

    _isInitialized = true;
  }

  bool isInitialized() => _isInitialized;

  Future<void> scheduleNotificationsForToday() async {
    if (!_isInitialized) await init();

    await _cancelAllNotifications();

    final todayTasks = taskManager.getTodayTasks();
    final notificationTimes = <DateTime, List<String>>{};

    for (final task in todayTasks) {
      if (task.isCompleted) continue;

      final dateStr = task.dueDate['date'] ?? '';
      final timeStr = task.dueDate['time'] ?? '';

      if (dateStr.isEmpty) continue;

      if (task.isDailyTask()) {
        _scheduleDailyTaskNotifications(task, dateStr, notificationTimes);
      } else {
        _scheduleTimedTaskNotifications(task, dateStr, timeStr, notificationTimes);
      }
    }

    await _sendScheduledNotifications(notificationTimes);
  }

  void _scheduleDailyTaskNotifications(
    Task task,
    String dateStr,
    Map<DateTime, List<String>> notificationTimes,
  ) {
    final today = DateFormat('yyyy-MM-dd').parse(dateStr);

    final morningTime = DateTime(today.year, today.month, today.day, 8, 0);
    final noonTime = DateTime(today.year, today.month, today.day, 12, 0);
    final eveningTime = DateTime(today.year, today.month, today.day, 18, 0);

    final now = DateTime.now();

    if (morningTime.isAfter(now)) {
      notificationTimes.putIfAbsent(morningTime, () => []).add(task.title);
    }
    if (noonTime.isAfter(now)) {
      notificationTimes.putIfAbsent(noonTime, () => []).add(task.title);
    }
    if (eveningTime.isAfter(now)) {
      notificationTimes.putIfAbsent(eveningTime, () => []).add(task.title);
    }
  }

  void _scheduleTimedTaskNotifications(
    Task task,
    String dateStr,
    String timeStr,
    Map<DateTime, List<String>> notificationTimes,
  ) {
    final today = DateFormat('yyyy-MM-dd').parse(dateStr);
    final timeParts = timeStr.split(':');
    if (timeParts.length != 2) return;

    final hour = int.tryParse(timeParts[0]) ?? 0;
    final minute = int.tryParse(timeParts[1]) ?? 0;

    final dueTime = DateTime(today.year, today.month, today.day, hour, minute);
    final oneHourBefore = dueTime.subtract(const Duration(hours: 1));

    final now = DateTime.now();

    if (oneHourBefore.isAfter(now)) {
      notificationTimes.putIfAbsent(oneHourBefore, () => []).add(task.title);
    }
    if (dueTime.isAfter(now)) {
      notificationTimes.putIfAbsent(dueTime, () => []).add(task.title);
    }
  }

  Future<void> _sendScheduledNotifications(
    Map<DateTime, List<String>> notificationTimes,
  ) async {
    int notificationId = 0;
    final location = tz.local;

    for (final entry in notificationTimes.entries) {
      final scheduledTime = entry.key;
      final taskTitles = entry.value;

      if (taskTitles.isEmpty) continue;

      final String title;
      final String body;

      if (taskTitles.length == 1) {
        title = '任务提醒';
        body = '「${taskTitles[0]}」';
      } else {
        title = '任务提醒';
        body = '您有 ${taskTitles.length} 个任务待处理：${taskTitles.join('、')}';
      }

      final tzTime = tz.TZDateTime.from(scheduledTime, location);

      await _flutterLocalNotificationsPlugin.zonedSchedule(
        id: notificationId++,
        title: title,
        body: body,
        scheduledDate: tzTime,
        notificationDetails: const NotificationDetails(
          android: AndroidNotificationDetails(
            'reminder_channel',
            '任务提醒',
            channelDescription: '任务截止时间提醒',
            importance: Importance.high,
            priority: Priority.high,
          ),
        ),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      );
    }
  }

  Future<void> _cancelAllNotifications() async {
    await _flutterLocalNotificationsPlugin.cancelAll();
  }

  Future<void> showImmediateNotification(String title, String body) async {
    if (!_isInitialized) await init();

    await _flutterLocalNotificationsPlugin.show(
      id: DateTime.now().millisecondsSinceEpoch,
      title: title,
      body: body,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          'reminder_channel',
          '任务提醒',
          channelDescription: '任务截止时间提醒',
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
    );
  }
}

final notificationService = NotificationService();
