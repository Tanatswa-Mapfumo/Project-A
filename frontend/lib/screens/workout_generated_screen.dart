import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/coach_speech_bubble.dart';
import '../widgets/deep_insight_panel.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/primary_button.dart';
import '../widgets/simple_app_bar.dart';

/// "workout-generated" — Figma node 37:296.
///
/// The exercise names, set/rep counts, weights, and chip labels ("45 Mins",
/// "Hard Effort") came through verbatim as literal layer names in the
/// metadata. The screen title, workout category/title, and coach message
/// are inferred (only generic layer names for those — the rate limit hit
/// before get_design_context could reveal the real copy).
class WorkoutGeneratedScreen extends StatelessWidget {
  const WorkoutGeneratedScreen({super.key});

  static const _exercises = [
    _Exercise('1. Barbell Bench Press', '3 Sets × 8 Reps', '135 lbs'),
    _Exercise('2. Dumbbell Overhead Press', '3 Sets × 10 Reps', '35 lbs ea'),
    _Exercise('3. Overhead Tricep Extension', '3 Sets × 12 Reps', '25 lbs'),
    _Exercise('4. Hanging Leg Raise', '3 Sets × Max Reps', 'Bodyweight'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const SimpleAppBar(title: "Today's Workout"),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Push Day',
                            style: GoogleFonts.dmSans(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.primary),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Chest, Shoulders & Triceps',
                            style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.ink),
                          ),
                          const SizedBox(height: 12),
                          const Wrap(
                            spacing: 8,
                            children: [
                              _Chip(label: '45 Mins'),
                              _Chip(label: 'Hard Effort'),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    const CoachSpeechBubble(
                      message: 'Your recovery scores are strong today, so I bumped the intensity up a notch.',
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'Exercises',
                      style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.ink),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        children: [
                          for (var i = 0; i < _exercises.length; i++) ...[
                            if (i != 0) const Divider(height: 1, color: AppColors.border),
                            _ExerciseRow(exercise: _exercises[i]),
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
                onPressed: () => Navigator.of(context)
                    .popUntil((route) => route.settings.name == 'dashboard'),
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

class _Exercise {
  const _Exercise(this.name, this.sets, this.weight);
  final String name;
  final String sets;
  final String weight;
}

class _ExerciseRow extends StatelessWidget {
  const _ExerciseRow({required this.exercise});

  final _Exercise exercise;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  exercise.name,
                  style: GoogleFonts.dmSans(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.ink),
                ),
                const SizedBox(height: 4),
                Text(
                  exercise.sets,
                  style: GoogleFonts.dmSans(fontSize: 12, color: AppColors.muted),
                ),
              ],
            ),
          ),
          Text(
            exercise.weight,
            style: GoogleFonts.dmSans(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.ink),
          ),
        ],
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
