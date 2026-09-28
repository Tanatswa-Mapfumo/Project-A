import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/coach_speech_bubble.dart';
import '../widgets/metric_slider.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/primary_button.dart';
import '../widgets/simple_app_bar.dart';
import 'workout_generated_screen.dart';

/// "daily-check-in" — Figma node 37:234.
///
/// The returning-user check-in (as opposed to the onboarding
/// "baseline-check-in"). Slider labels are inferred, but the starting
/// values are real — the metadata's slider-fill widths (274, 239, 274,
/// 103, 171 out of 342) work out to clean 8/7/8/3/5 out of 10. The
/// soreness-card copy ("No active soreness logged" / "Tap to modify
/// active sore spots") came through verbatim.
class DailyCheckInScreen extends StatefulWidget {
  const DailyCheckInScreen({super.key});

  @override
  State<DailyCheckInScreen> createState() => _DailyCheckInScreenState();
}

class _DailyCheckInScreenState extends State<DailyCheckInScreen> {
  final Map<String, double> _metrics = {
    'Energy': 8,
    'Sleep Quality': 7,
    'Motivation': 8,
    'Stress': 3,
    'Recovery': 5,
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const SimpleAppBar(title: 'Daily Check-In'),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const CoachSpeechBubble(
                      message: 'How are you feeling today?',
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
                      'Soreness Check',
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
                              width: 56,
                              height: 56,
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(14),
                              ),
                              child: const Icon(Icons.accessibility_new, size: 24, color: AppColors.primary),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'No active soreness logged',
                                    style: GoogleFonts.dmSans(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.ink),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Tap to modify active sore spots',
                                    style: GoogleFonts.dmSans(fontSize: 12, height: 1.3, color: AppColors.muted),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            OnboardingActionArea(
              primary: PrimaryButton(
                label: "Generate Today's Workout",
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const WorkoutGeneratedScreen()),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
