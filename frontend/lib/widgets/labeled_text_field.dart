import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';

/// A label above a 52px rounded input ("form-field-*" in Figma).
class LabeledTextField extends StatelessWidget {
  const LabeledTextField({
    super.key,
    required this.label,
    this.controller,
    this.obscureText = false,
    this.trailing,
    this.hintText,
    this.readOnly = false,
    this.onTap,
    this.keyboardType,
  });

  final String label;
  final TextEditingController? controller;
  final bool obscureText;
  final Widget? trailing;
  final String? hintText;
  final bool readOnly;
  final VoidCallback? onTap;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.dmSans(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: AppColors.ink,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          height: 52,
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.border),
          ),
          child: TextField(
            controller: controller,
            obscureText: obscureText,
            readOnly: readOnly,
            onTap: onTap,
            keyboardType: keyboardType,
            style: GoogleFonts.dmSans(fontSize: 15, color: AppColors.ink),
            decoration: InputDecoration(
              border: InputBorder.none,
              hintText: hintText,
              hintStyle: GoogleFonts.dmSans(fontSize: 15, color: AppColors.muted),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              suffixIcon: trailing,
            ),
          ),
        ),
      ],
    );
  }
}
