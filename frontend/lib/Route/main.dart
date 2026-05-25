
import 'package:flutter/material.dart';
import 'package:reminder/Page/HomePage.dart';

Widget getRootWidget() {
  return MaterialApp(
    routes: getRootRoutes(),
  );
}

Map<String, WidgetBuilder> getRootRoutes() {
  return {
    '/': (context) => const HomePage(),
  };
}