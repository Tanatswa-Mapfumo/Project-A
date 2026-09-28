import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import 'daily_checkin_screen.dart';

/// "home-dashboard" — Figma node 37:170.
///
/// The greeting/user name, streak count wording, and consistency-card copy
/// came through verbatim in the metadata. "today-workout-card" had no
/// children captured (an empty frame in the metadata, possibly a
/// component instance the tool didn't expand), so that card's content
/// below is an inferred placeholder. The bottom tab bar (Home / Progress /
/// Settings) is real structure — only Home has a designed screen behind
/// it; Progress and Settings just show "coming soon" placeholders.
class HomeDashboardScreen extends StatefulWidget {
  const HomeDashboardScreen({super.key});

  @override
  State<HomeDashboardScreen> createState() => _HomeDashboardScreenState();
}

class _HomeDashboardScreenState extends State<HomeDashboardScreen> {
  int _tabIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: IndexedStack(
          index: _tabIndex,
          children: const [
            _DashboardHomeTab(),
            _PlaceholderTab(label: 'Progress'),
            _PlaceholderTab(label: 'Settings'),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: _BottomTabBar(
          index: _tabIndex,
          onChanged: (i) => setState(() => _tabIndex = i),
        ),
      ),
    );
  }
}

class _DashboardHomeTab extends StatelessWidget {
  const _DashboardHomeTab();

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.centerLeft,
                    end: Alignment.centerRight,
                    colors: [AppColors.primaryLight, AppColors.primary],
                  ),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.person, size: 20, color: Colors.white),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Welcome back',
                      style: GoogleFonts.dmSans(fontSize: 12, color: AppColors.muted),
                    ),
                    Text(
                      'Jordan',
                      style: GoogleFonts.outfit(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.ink),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(100),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.local_fire_department, size: 16, color: AppColors.primary),
                    const SizedBox(width: 4),
                    Text(
                      '5 Days',
                      style: GoogleFonts.dmSans(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.primary),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          InkWell(
            borderRadius: BorderRadius.circular(20),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const DailyCheckInScreen()),
            ),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.tune, size: 20, color: AppColors.primary),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Check in for today's plan",
                          style: GoogleFonts.dmSans(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.ink),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Help us adapt your session to your current recovery',
                          style: GoogleFonts.dmSans(fontSize: 12, height: 1.3, color: AppColors.muted),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: AppColors.muted),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
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
                  "Today's Workout",
                  style: GoogleFonts.dmSans(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.primary),
                ),
                const SizedBox(height: 4),
                Text(
                  'Not generated yet',
                  style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.ink),
                ),
                const SizedBox(height: 4),
                Text(
                  'Check in above to generate today’s session.',
                  style: GoogleFonts.dmSans(fontSize: 13, color: AppColors.muted),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.border),
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
                  child: const Icon(Icons.emoji_events, size: 24, color: AppColors.primary),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Consistency Score: 94%',
                        style: GoogleFonts.dmSans(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.ink),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Keep your daily check-in streak going!',
                        style: GoogleFonts.dmSans(fontSize: 12, height: 1.3, color: AppColors.muted),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PlaceholderTab extends StatelessWidget {
  const _PlaceholderTab({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        '$label coming soon',
        style: GoogleFonts.dmSans(fontSize: 15, color: AppColors.muted),
      ),
    );
  }
}

class _BottomTabBar extends StatelessWidget {
  const _BottomTabBar({required this.index, required this.onChanged});

  final int index;
  final ValueChanged<int> onChanged;

  static const _tabs = [
    (Icons.home, 'Home'),
    (Icons.show_chart, 'Progress'),
    (Icons.settings, 'Settings'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 64,
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          for (var i = 0; i < _tabs.length; i++)
            Expanded(
              child: InkWell(
                onTap: () => onChanged(i),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _tabs[i].$1,
                      size: 24,
                      color: index == i ? AppColors.primary : AppColors.muted,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _tabs[i].$2,
                      style: GoogleFonts.dmSans(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: index == i ? AppColors.primary : AppColors.muted,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
