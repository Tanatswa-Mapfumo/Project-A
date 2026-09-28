import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

/// The decorative gesture-bar pill at the bottom of every screen
/// (Figma: "home-indicator-container" / "indicator-bar", 139x5, radius 100).
class HomeIndicator extends StatelessWidget {
  const HomeIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Container(
        width: 139,
        height: 5,
        decoration: BoxDecoration(
          color: AppColors.ink,
          borderRadius: BorderRadius.circular(100),
        ),
      ),
    );
  }
}
