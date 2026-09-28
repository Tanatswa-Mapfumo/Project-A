import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/coach_speech_bubble.dart';
import '../widgets/metric_slider.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/onboarding_header.dart';
import '../widgets/primary_button.dart';
import 'first_workout_preview_screen.dart';

/// "baseline-check-in" — Figma node 37:65.
///
/// Slider labels are inferred, but the starting *values* are real: the
/// metadata's slider-fill widths (239, 274, 205, 137 out of a 342 track)
/// work out to clean 7/8/6/4 out of 10, so those are reproduced exactly.
class BaselineCheckInScreen extends StatefulWidget {
  const BaselineCheckInScreen({super.key});

  @override
  State<BaselineCheckInScreen> createState() => _BaselineCheckInScreenState();
}

class _BaselineCheckInScreenState extends State<BaselineCheckInScreen> {
  final Map<String, double> _metrics = {
    'Energy': 7,
    'Sleep Quality': 8,
    'Stress': 6,
    'Motivation': 4,
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const OnboardingHeader(
              title: 'Baseline Check-In',
              subtitle: 'Quick check-in before we build today’s session.',
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const CoachSpeechBubble(
                      message: 'Be honest — this just helps me pace today right.',
                    ),
                    const SizedBox(height: 20),
                    for (final entry in _metrics.entries) ...[
                      MetricSlider(
                        label: entry.key,
                        value: entry.value,
                        onChanged: (v) => setState(() => _metrics[entry.key] = v),
                      ),
                      const SizedBox(height: 16),
                    ],
                    const SizedBox(height: 4),
                    Text(
                      'Any soreness today?',
                      style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.ink),
                    ),
                    const SizedBox(height: 12),
                    InkWell(
                      borderRadius: BorderRadius.circular(20),
                      onTap: () => ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Body map coming soon.')),
                      ),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 72,
                              height: 72,
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: const Icon(Icons.accessibility_new, size: 32, color: AppColors.primary),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Tap to log soreness',
                                    style: GoogleFonts.dmSans(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.ink),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Specify targeted areas like shoulders or lower back',
                                    style: GoogleFonts.dmSans(fontSize: 12, height: 1.3, color: AppColors.muted),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    Align(
                      alignment: Alignment.center,
                      child: TextButton(
                        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Pain detail logging coming soon.')),
                        ),
                        child: Text(
                          '+ Add pain details',
                          style: GoogleFonts.dmSans(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.primary),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            OnboardingActionArea(
              primary: PrimaryButton(
                label: 'Generate First Workout',
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const FirstWorkoutPreviewScreen()),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
