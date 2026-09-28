import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import 'login_screen.dart';
import 'signup_screen.dart';

/// "welcome" screen — Figma node 33:5, frame size 390x844.
///
/// The Figma frame includes a fake iOS status bar (9:41 / signal / wifi /
/// battery) and a fake home-indicator pill. Those are artboard chrome the
/// designer added so the mockup reads as a real phone, not app UI — a real
/// build can't draw the correct time/battery anyway, so this screen instead
/// makes the real status bar transparent with light icons over the photo
/// and reserves the same 44px of vertical space, matching the design's
/// layout exactly without faking system state. The home-indicator pill is
/// kept since it's just a decorative shape, not system-owned.
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
        statusBarBrightness: Brightness.dark,
      ),
      child: Scaffold(
        backgroundColor: Colors.black,
        body: Stack(
          fit: StackFit.expand,
          children: [
            Opacity(
              opacity: 0.8,
              child: Image.asset(
                'assets/images/welcome_bg.jpg',
                fit: BoxFit.cover,
              ),
            ),
            const SafeArea(
              bottom: false,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  SizedBox(height: 44),
                  _TopContent(),
                  _BottomCtas(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TopContent extends StatelessWidget {
  const _TopContent();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 40, left: 24, right: 24),
      child: Column(
        children: [
          Container(
            width: 96,
            height: 96,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(28),
              gradient: const LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [AppColors.primaryLight, AppColors.primary],
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.primary.withValues(alpha: 0.2),
                  blurRadius: 12,
                  offset: const Offset(0, 12),
                ),
              ],
            ),
            child: SvgPicture.asset(
              'assets/icons/chart_spline.svg',
              width: 48,
              height: 48,
              colorFilter: const ColorFilter.mode(Colors.white, BlendMode.srcIn),
            ),
          ),
          const SizedBox(height: 48),
          Text(
            'Your adaptive fitness coach — built around your real life.',
            textAlign: TextAlign.center,
            style: GoogleFonts.outfit(
              fontSize: 32,
              fontWeight: FontWeight.w700,
              height: 1.2,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}

class _BottomCtas extends StatelessWidget {
  const _BottomCtas();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
      child: Column(
        children: [
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SignupScreen()),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                elevation: 0,
                shadowColor: Colors.transparent,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(28),
                ),
              ),
              child: Text(
                'Get Started',
                style: GoogleFonts.dmSans(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 48,
            child: Center(
              child: GestureDetector(
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                ),
                child: RichText(
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: 'Already have an account? ',
                        style: GoogleFonts.dmSans(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                      TextSpan(
                        text: 'Log In',
                        style: GoogleFonts.dmSans(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: AppColors.primary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Container(
              width: 139,
              height: 5,
              decoration: BoxDecoration(
                color: AppColors.ink,
                borderRadius: BorderRadius.circular(100),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
