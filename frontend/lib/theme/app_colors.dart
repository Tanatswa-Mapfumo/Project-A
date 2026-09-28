import 'package:flutter/material.dart';

/// Design tokens pulled directly from the Figma file
/// (App designs, node 33:5 — "welcome").
class AppColors {
  AppColors._();

  static const primary = Color(0xFFFF5A36);
  static const primaryLight = Color(0xFFFF8166);
  static const ink = Color(0xFF1E1E1C);
  static const muted = Color(0xFF646360);
  static const border = Color(0xFFE2DFD9);

  /// Not sampled from Figma (rate-limited before these screens' fills could
  /// be pulled) — light neutrals consistent with [border] and [ink].
  static const background = Colors.white;
  static const surface = Color(0xFFF7F5F2);
}
