import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/coach_speech_bubble.dart';
import '../widgets/deep_insight_panel.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/onboarding_header.dart';
import '../widgets/primary_button.dart';
import 'home_dashboard_screen.dart';

/// "first-workout-preview" — Figma node 37:124.
///
/// The chip labels ("35 Mins", "Moderate Intensity"), the "What we will
/// cover:" heading, its three bullet items, and the "Start Workout" button
/// text all came through verbatim as literal layer names in the metadata.
/// The workout category/title and coach message are inferred.
///
/// "Start Workout" completes onboarding into the home dashboard (node
/// 37:170, fetched later) rather than a workout-player screen, since none
/// was designed. "Why this workout?" now opens the real insight panel
/// (node 37:351) instead of the placeholder text sheet this used to show.
class FirstWorkoutPreviewScreen extends StatelessWidget {
  const FirstWorkoutPreviewScreen({super.key});

  static const _briefItems = [
    'Mobility warmup to lubricate joints',
    'Core stability & bodyweight patterns',
    'Guided cooldown stretching',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const OnboardingHeader(
              title: 'Your First Workout Is Ready',
              subtitle: "Here's what I've put together based on everything you shared.",
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const CoachSpeechBubble(
                      message: "Let's start easy today and build from here.",
                    ),
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Full Body',
                            style: GoogleFonts.dmSans(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.primary),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Foundational Strength & Mobility',
                            style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.ink),
                          ),
                          const SizedBox(height: 12),
                          const Wrap(
                            spacing: 8,
                            children: [
                              _Chip(label: '35 Mins'),
                              _Chip(label: 'Moderate Intensity'),
                            ],
                          ),
                          const SizedBox(height: 16),
                          const Divider(height: 1, color: AppColors.border),
                          const SizedBox(height: 16),
                          Text(
                            'What we will cover:',
                            style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.ink),
                          ),
                          const SizedBox(height: 12),
                          for (final item in _briefItems) ...[
                            Padding(
                              padding: const EdgeInsets.only(bottom: 10),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(Icons.check_circle, size: 16, color: AppColors.primary),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      item,
                                      style: GoogleFonts.dmSans(fontSize: 14, height: 1.3, color: AppColors.ink),
                                    ),
                                  ),
                                ],
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
                label: 'Start Workout',
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    settings: const RouteSettings(name: 'dashboard'),
                    builder: (_) => const HomeDashboardScreen(),
                  ),
                ),
              ),
              secondary: Center(
                child: TextButton(
                  onPressed: () => DeepInsightPanel.show(context),
                  child: Text(
                    'Why this workout?',
                    style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.primary),
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

class _Chip extends StatelessWidget {
  const _Chip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: GoogleFonts.dmSans(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.primary),
      ),
    );
  }
}
