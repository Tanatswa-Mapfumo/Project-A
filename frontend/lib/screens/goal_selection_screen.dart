import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import '../widgets/onboarding_action_area.dart';
import '../widgets/onboarding_header.dart';
import '../widgets/primary_button.dart';
import 'training_profile_screen.dart';

/// "goal-selection" — Figma node 34:45.
///
/// Frame names in the metadata ("goal-card-lose-fat", "-gain-muscle",
/// "-get-stronger", "-improve-mobility") gave real labels; icon glyphs are
/// Material approximations of Figma's exported icons (zap-off, dumbbell,
/// zap, activity) since those assets weren't fetched before the rate limit.
class GoalSelectionScreen extends StatefulWidget {
  const GoalSelectionScreen({super.key});

  @override
  State<GoalSelectionScreen> createState() => _GoalSelectionScreenState();
}

class _Goal {
  const _Goal(this.label, this.icon);
  final String label;
  final IconData icon;
}

class _GoalSelectionScreenState extends State<GoalSelectionScreen> {
  static const _goals = [
    _Goal('Lose Fat', Icons.flash_off),
    _Goal('Gain Muscle', Icons.fitness_center),
    _Goal('Get Stronger', Icons.bolt),
    _Goal('Improve Mobility', Icons.accessibility_new),
  ];

  int? _selected;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const OnboardingHeader(
              progressLabel: 'Step 2 of 3',
              title: "What's your main goal?",
              subtitle: "We'll tailor your plan around this.",
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                child: Column(
                  children: [
                    for (var i = 0; i < _goals.length; i++) ...[
                      if (i != 0) const SizedBox(height: 12),
                      _GoalCard(
                        goal: _goals[i],
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
                label: 'Continue',
                enabled: _selected != null,
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const TrainingProfileScreen()),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GoalCard extends StatelessWidget {
  const _GoalCard({required this.goal, required this.selected, required this.onTap});

  final _Goal goal;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: onTap,
      child: Container(
        height: 76,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? AppColors.primary : AppColors.border, width: selected ? 2 : 1),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(goal.icon, size: 22, color: AppColors.primary),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                goal.label,
                style: GoogleFonts.dmSans(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.ink),
              ),
            ),
            Container(
              width: 20,
              height: 20,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: selected ? AppColors.primary : Colors.transparent,
                border: Border.all(color: selected ? AppColors.primary : AppColors.border, width: 1.5),
              ),
              child: selected
                  ? const Icon(Icons.check, size: 12, color: Colors.white)
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}
