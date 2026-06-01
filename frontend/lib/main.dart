import 'package:flutter/material.dart';
import 'package:reminder/Route/main.dart';
import 'package:reminder/stores/TokenManager.dart';
import 'package:reminder/stores/LoginManager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await tokenManager.removeToken();
  await loginManager.logout();
  
  runApp(getRootWidget());
}

