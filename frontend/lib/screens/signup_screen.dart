import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/labeled_text_field.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/onboarding_header.dart';
import '../widgets/primary_button.dart';
import 'goal_selection_screen.dart';
import 'login_screen.dart';

/// "account-creation" — Figma node 33:24.
///
/// Title/subtitle/field placeholder copy is inferred (the metadata only
/// exposed generic layer names for those); button and link text below
/// ("Continue", "Already have an account? Log in") came through verbatim.
class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _countryController = TextEditingController();
  bool _obscurePassword = true;

  static const _countries = [
    'United States',
    'United Kingdom',
    'Canada',
    'Australia',
    'Ghana',
    'Nigeria',
    'Germany',
    'France',
    'India',
    'Japan',
  ];

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _countryController.dispose();
    super.dispose();
  }

  Future<void> _pickCountry() async {
    final selected = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: AppColors.background,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        return SafeArea(
          child: ListView(
            shrinkWrap: true,
            children: _countries
                .map((country) => ListTile(
                      title: Text(country, style: GoogleFonts.dmSans(fontSize: 15)),
                      onTap: () => Navigator.of(context).pop(country),
                    ))
                .toList(),
          ),
        );
      },
    );
    if (selected != null) {
      setState(() => _countryController.text = selected);
    }
  }

  void _onContinue() {
    if (_nameController.text.trim().isEmpty ||
        _emailController.text.trim().isEmpty ||
        _passwordController.text.trim().isEmpty ||
        _countryController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill in all fields to continue.')),
      );
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const GoalSelectionScreen()),
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
              progressLabel: 'Step 1 of 3',
              title: 'Create your account',
              subtitle: "Tell us a bit about you so we can personalize your plan.",
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  children: [
                    LabeledTextField(label: 'Name', controller: _nameController),
                    const SizedBox(height: 12),
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
                    const SizedBox(height: 12),
                    LabeledTextField(
                      label: 'Country',
                      controller: _countryController,
                      readOnly: true,
                      onTap: _pickCountry,
                      hintText: 'Select your country',
                      trailing: const Icon(Icons.keyboard_arrow_down, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
            ),
            OnboardingActionArea(
              primary: PrimaryButton(label: 'Continue', onPressed: _onContinue),
              secondary: GestureDetector(
                onTap: () => Navigator.of(context).pushReplacement(
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                ),
                child: RichText(
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: 'Already have an account? ',
                        style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.muted),
                      ),
                      TextSpan(
                        text: 'Log in',
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
