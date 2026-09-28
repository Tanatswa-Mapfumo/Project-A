import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/onboarding_header.dart';
import '../widgets/primary_button.dart';
import 'accessibility_preferences_screen.dart';

/// "training-profile" — Figma node 34:92.
///
/// "Intermediate" ships pre-selected because its radio node was the only
/// one with a filled center dot in the metadata. Descriptions are inferred
/// (only the level names came through the layer names; the description
/// text itself needs get_design_context, which was rate-limited).
class TrainingProfileScreen extends StatefulWidget {
  const TrainingProfileScreen({super.key});

  @override
  State<TrainingProfileScreen> createState() => _TrainingProfileScreenState();
}

class _Level {
  const _Level(this.label, this.description);
  final String label;
  final String description;
}

class _TrainingProfileScreenState extends State<TrainingProfileScreen> {
  static const _levels = [
    _Level('Beginner', 'New to structured training, or just getting back into it.'),
    _Level('Intermediate', 'Training consistently for 6+ months with a decent base.'),
    _Level('Advanced', 'Years of consistent training experience.'),
  ];

  int _selected = 1;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const OnboardingHeader(
              progressLabel: 'Step 3 of 3',
              title: 'Tell us your experience level',
              subtitle: 'This helps us calibrate difficulty from day one.',
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Experience Level',
                      style: GoogleFonts.dmSans(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.ink),
                    ),
                    const SizedBox(height: 12),
                    for (var i = 0; i < _levels.length; i++) ...[
                      if (i != 0) const SizedBox(height: 12),
                      _LevelCard(
                        level: _levels[i],
                        selected: _selected == i,
                        onTap: () => setState(() => _selected = i),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            OnboardingActionArea(
              primary: PrimaryButton(
                label: 'Complete Profile',
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const AccessibilityPreferencesScreen()),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LevelCard extends StatelessWidget {
  const _LevelCard({required this.level, required this.selected, required this.onTap});

  final _Level level;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? AppColors.primary : AppColors.border, width: selected ? 2 : 1),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    level.label,
                    style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.ink),
                  ),
                ),
                Container(
                  width: 18,
                  height: 18,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: selected ? AppColors.primary : AppColors.border, width: 1.5),
                  ),
                  child: selected
                      ? Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(shape: BoxShape.circle, color: AppColors.primary),
                        )
                      : null,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              level.description,
              style: GoogleFonts.dmSans(fontSize: 13, height: 1.4, color: AppColors.muted),
            ),
          ],
        ),
      ),
    );
  }
}
