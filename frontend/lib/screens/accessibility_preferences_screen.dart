import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/coach_speech_bubble.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/onboarding_header.dart';
import '../widgets/primary_button.dart';
import 'baseline_checkin_screen.dart';

/// "accessibility-preferences" — Figma node 37:11.
///
/// Toggle labels are inferred (the metadata's toggle-row text nodes were
/// generic, and the rate limit hit before get_design_context could reveal
/// the real copy). The on/off defaults, though, are real: they're read
/// straight off each toggle-knob's x position in the metadata.
class AccessibilityPreferencesScreen extends StatefulWidget {
  const AccessibilityPreferencesScreen({super.key});

  @override
  State<AccessibilityPreferencesScreen> createState() => _AccessibilityPreferencesScreenState();
}

class _AccessibilityPreferencesScreenState extends State<AccessibilityPreferencesScreen> {
  final List<String> _labels = const [
    'Reduce motion',
    'Voice guidance',
    'Larger text',
    'Haptic feedback',
    'High contrast mode',
    'Screen reader support',
  ];

  // Matches each row's toggle-knob x-offset in the Figma metadata
  // (x=2 -> off, x=22 -> on).
  final List<bool> _values = [false, true, false, true, false, true];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const OnboardingHeader(
              title: 'Accessibility Preferences',
              subtitle: "Let's make sure the app works great for you.",
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  children: [
                    const CoachSpeechBubble(
                      message: 'You can change any of these later in Settings.',
                    ),
                    const SizedBox(height: 20),
                    Container(
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        children: [
                          for (var i = 0; i < _labels.length; i++) ...[
                            if (i != 0) const Divider(height: 1, color: AppColors.border),
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 16),
                              child: SwitchListTile(
                                contentPadding: EdgeInsets.zero,
                                title: Text(
                                  _labels[i],
                                  style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w500, color: AppColors.ink),
                                ),
                                value: _values[i],
                                activeThumbColor: Colors.white,
                                activeTrackColor: AppColors.primary,
                                onChanged: (value) => setState(() => _values[i] = value),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            OnboardingActionArea(
              primary: PrimaryButton(
                label: 'Continue',
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const BaselineCheckInScreen()),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
