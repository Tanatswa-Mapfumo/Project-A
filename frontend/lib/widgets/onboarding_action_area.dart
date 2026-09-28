import 'package:flutter/material.dart';

import 'home_indicator.dart';

/// The bottom CTA block shared by every onboarding screen: primary button,
/// optional secondary row (a text link), then the home-indicator pill.
class OnboardingActionArea extends StatelessWidget {
  const OnboardingActionArea({super.key, required this.primary, this.secondary});

  final Widget primary;
  final Widget? secondary;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
      child: Column(
        children: [
          primary,
          if (secondary != null) ...[
            const SizedBox(height: 16),
            secondary!,
          ],
          const SizedBox(height: 16),
          const HomeIndicator(),
        ],
      ),
    );
  }
}
