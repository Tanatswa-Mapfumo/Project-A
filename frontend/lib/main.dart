import 'package:flutter/material.dart';

import 'screens/welcome_screen.dart';

void main() {
  runApp(const AppDesignsApp());
}

class AppDesignsApp extends StatelessWidget {
  const AppDesignsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'App designs',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(useMaterial3: true),
      home: const WelcomeScreen(),
    );
  }
}
