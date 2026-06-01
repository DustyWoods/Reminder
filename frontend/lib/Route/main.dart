
import 'package:flutter/material.dart';
import 'package:reminder/Page/HomePage.dart';
import 'package:reminder/Page/LoginPage.dart';
import 'package:reminder/Page/RegisterPage.dart';

Widget getRootWidget() {
  return MaterialApp(
    routes: getRootRoutes(),
  );
}

Map<String, WidgetBuilder> getRootRoutes() {
  return {
    '/': (context) => const HomePage(),
    '/login': (cntext) => const LoginPage(),
    '/register': (context) => const RegisterPage(),
  };
}