import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../theme/app_colors.dart';
import 'coach_speech_bubble.dart';

/// "deep-insight-panel" — Figma node 37:351.
///
/// A modal sheet with 5 expandable insight cards (accordion, one open at a
/// time). The first card's full body text ("Your HRV & resting heart
/// rate...") came through verbatim in the metadata; the other 4 bodies and
/// the coach-speech message are inferred placeholders — the rate limit hit
/// before get_design_context could reveal them.
class DeepInsightPanel extends StatefulWidget {
  const DeepInsightPanel({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const DeepInsightPanel(),
    );
  }

  @override
  State<DeepInsightPanel> createState() => _DeepInsightPanelState();
}

class _Insight {
  const _Insight(this.title, this.icon, this.body);
  final String title;
  final IconData icon;
  final String body;
}

class _DeepInsightPanelState extends State<DeepInsightPanel> {
  static const _insights = [
    _Insight(
      'Recovery Insight',
      Icons.favorite,
      'Your HRV & resting heart rate are highly favorable today. The physiological data indicates a 92% readiness score, permitting higher CNS load and metabolic stress safely.',
    ),
    _Insight(
      'Energy Trend',
      Icons.bolt,
      'Your logged energy has trended upward over the past few check-ins, which supports today’s heavier session.',
    ),
    _Insight(
      'Soreness Analysis',
      Icons.monitor_heart,
      'No active soreness spots are logged right now, so today’s plan doesn’t need to route around anything.',
    ),
    _Insight(
      'Burnout Risk',
      Icons.warning_amber_rounded,
      'Your training load is well within a sustainable range — no signs of accumulating fatigue.',
    ),
    _Insight(
      'Long-Term Progression',
      Icons.trending_up,
      'You’re on pace with the strength gains we planned for this phase. Keep the current cadence going.',
    ),
  ];

  int _expanded = 0;

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.86,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: AppColors.background,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: ListView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(
                      'Why This Workout?',
                      style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.ink),
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.close, color: AppColors.muted),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const CoachSpeechBubble(
                message: 'Here’s the data behind today’s plan.',
              ),
              const SizedBox(height: 16),
              for (var i = 0; i < _insights.length; i++) ...[
                if (i != 0) const SizedBox(height: 12),
                _InsightCard(
                  insight: _insights[i],
                  expanded: _expanded == i,
                  onTap: () => setState(() => _expanded = _expanded == i ? -1 : i),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}

class _InsightCard extends StatelessWidget {
  const _InsightCard({required this.insight, required this.expanded, required this.onTap});

  final _Insight insight;
  final bool expanded;
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
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(insight.icon, size: 20, color: AppColors.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    insight.title,
                    style: GoogleFonts.dmSans(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.ink),
                  ),
                ),
                Icon(
                  expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                  color: AppColors.muted,
                ),
              ],
            ),
            if (expanded) ...[
              const SizedBox(height: 12),
              Text(
                insight.body,
                style: GoogleFonts.dmSans(fontSize: 14, height: 1.4, color: AppColors.muted),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
