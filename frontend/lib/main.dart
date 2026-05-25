import 'package:flutter/material.dart';
import 'package:reminder/Route/main.dart';
import 'package:reminder/stores/TokenManager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await tokenManager.removeToken();
  runApp(getRootWidget());
}

