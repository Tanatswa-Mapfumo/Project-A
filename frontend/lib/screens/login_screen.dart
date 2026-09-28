import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/labeled_text_field.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/onboarding_header.dart';
import '../widgets/primary_button.dart';
import 'home_dashboard_screen.dart';
import 'signup_screen.dart';

/// "login" — Figma node 34:6.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _onLogIn() {
    if (_emailController.text.trim().isEmpty || _passwordController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter your email and password to log in.')),
      );
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute(
        settings: const RouteSettings(name: 'dashboard'),
        builder: (_) => const HomeDashboardScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const OnboardingHeader(
              title: 'Welcome back',
              subtitle: "Log in to pick up right where you left off.",
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  children: [
                    LabeledTextField(
                      label: 'Email',
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                    ),
                    const SizedBox(height: 12),
                    LabeledTextField(
                      label: 'Password',
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      trailing: IconButton(
                        icon: Icon(
                          _obscurePassword ? Icons.visibility_off : Icons.visibility,
                          size: 20,
                          color: AppColors.muted,
                        ),
                        onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      ),
                    ),
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Password reset coming soon.')),
                        ),
                        child: Text(
                          'Forgot password?',
                          style: GoogleFonts.dmSans(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.muted),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            OnboardingActionArea(
              primary: PrimaryButton(label: 'Log In', onPressed: _onLogIn),
              secondary: GestureDetector(
                onTap: () => Navigator.of(context).pushReplacement(
                  MaterialPageRoute(builder: (_) => const SignupScreen()),
                ),
                child: RichText(
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: "Don't have an account? ",
                        style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.muted),
                      ),
                      TextSpan(
                        text: 'Sign up',
                        style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.primary),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
