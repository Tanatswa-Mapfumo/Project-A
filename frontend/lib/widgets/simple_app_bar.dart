import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';

/// Back button + inline title on one row ("header-bar" with a "title-label"
/// child, as opposed to [OnboardingHeader]'s separate title/subtitle block
/// below the header). Used by screens that don't have a subtitle.
class SimpleAppBar extends StatelessWidget {
  const SimpleAppBar({super.key, required this.title, this.onBack});

  final String title;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 64,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Row(
          children: [
            SizedBox(
              width: 40,
              height: 40,
              child: IconButton(
                padding: EdgeInsets.zero,
                onPressed: onBack ?? () => Navigator.of(context).maybePop(),
                icon: const Icon(Icons.arrow_back, size: 18, color: AppColors.ink),
              ),
            ),
            const SizedBox(width: 16),
            Text(
              title,
              style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.ink),
            ),
          ],
        ),
      ),
    );
  }
}
