"""Deterministic mock AI provider.

Produces template-based text from structured facts only. Used for tests and local
development so the full system works without any external AI dependency.
"""

import json

from app.ai.base import AIProviderError
from app.rules.config import FALLBACK_INTENSITY


class MockAIProvider:
    name = "mock"
    model = "mock-template-v1"

    async def generate_short_explanation(self, source_facts: dict, workout_plan: dict) -> str:
        return build_short_explanation(source_facts)

    async def generate_deep_insight(
        self,
        source_facts: dict,
        workout_plan: dict,
        history_summary: dict,
    ) -> dict:
        recovery = (source_facts.get("recovery") or {}).get("score")
        excluded = (source_facts.get("soreness") or {}).get("excluded_regions", [])
        deprioritized = (source_facts.get("soreness") or {}).get("deprioritized_regions", [])
        intensity = (source_facts.get("decisions") or {}).get("intensity", "moderate")
        goal = (source_facts.get("constraints") or {}).get("primary_goal", "your goal")
        energy = (source_facts.get("recovery") or {}).get("energy")

        soreness_text = (
            f"Highly sore areas today: {', '.join(excluded)}. Moderately sore: "
            f"{', '.join(deprioritized)}. Work was shifted away from these areas."
            if excluded or deprioritized
            else "No major soreness was reported today."
        )
        avg_energy = history_summary.get("avg_energy_7d")
        energy_trend_text = (
            f"Your 7-day average energy was {avg_energy}/10."
            if avg_energy is not None
            else "There is not enough history yet to show an energy trend."
        )
        consistency = history_summary.get("consistency_score")
        burnout_text = (
            f"With a recent consistency score of {consistency}% and energy at {energy}/10 "
            "today, burnout risk appears low to moderate. The engine kept intensity "
            f"{intensity} to stay sustainable."
            if consistency is not None and energy is not None
            else "Not enough history yet to assess burnout risk."
        )
        return {
            "sections": [
                {
                    "type": "recovery",
                    "title": "Recovery Insight",
                    "content": f"Your recovery score today was {recovery}/10, which drove the "
                    f"{intensity} intensity of this session.",
                },
                {
                    "type": "energy",
                    "title": "Energy Trend",
                    "content": f"Energy today was {energy}/10. {energy_trend_text}",
                },
                {
                    "type": "soreness",
                    "title": "Soreness Analysis",
                    "content": soreness_text,
                },
                {
                    "type": "burnout",
                    "title": "Burnout Risk",
                    "content": burnout_text,
                },
                {
                    "type": "progression",
                    "title": "Long-Term Progression Impact",
                    "content": f"This {workout_plan.get('type', '')} session at {intensity} "
                    f"intensity supports your {goal} goal while respecting recovery.",
                },
            ]
        }

    async def generate_weekly_insight(self, week_facts: dict) -> dict:
        metrics = week_facts.get("metrics", {})
        consistency = week_facts.get("consistency_score", 0)
        avg_recovery = metrics.get("avg_recovery")
        avg_energy = metrics.get("avg_energy")
        adjustments = week_facts.get("planned_adjustments", {})
        volume = adjustments.get("volume_direction", "maintain")
        return {
            "sections": [
                {
                    "type": "consistency",
                    "title": "Consistency",
                    "content": f"You completed {metrics.get('sessions_completed', 0)} of "
                    f"{metrics.get('sessions_planned', 0)} planned sessions "
                    f"({consistency}% consistency).",
                },
                {
                    "type": "recovery",
                    "title": "Recovery Pattern",
                    "content": f"Average recovery score for the week was {avg_recovery}/10."
                    if avg_recovery is not None
                    else "Not enough check-in data for a recovery pattern.",
                },
                {
                    "type": "energy",
                    "title": "Energy Trend",
                    "content": f"Average energy was {avg_energy}/10 for the week."
                    if avg_energy is not None
                    else "Not enough check-in data for an energy trend.",
                },
                {
                    "type": "adjustment",
                    "title": "Next Week Plan",
                    "content": f"Based on this week, the planned direction for next week is "
                    f"to {volume} training volume.",
                },
            ]
        }


def build_short_explanation(source_facts: dict) -> str:
    """Deterministic fallback explanation built from rule_trace (section 16.3)."""
    decisions = source_facts.get("decisions", {})
    soreness = source_facts.get("soreness", {})
    intensity = decisions.get("intensity", FALLBACK_INTENSITY.value)
    excluded = soreness.get("excluded_regions", [])
    if excluded:
        return (
            f"Today's plan uses {intensity} intensity based on your check-in and keeps "
            f"work away from your {', '.join(excluded)}."
        )
    return f"Today's plan uses {intensity} intensity based on your check-in."


def parse_json_sections(raw: str) -> dict:
    """Parse and structurally validate an LLM JSON response into insight sections."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AIProviderError("Provider output was not valid JSON.") from exc
    sections = data.get("sections") if isinstance(data, dict) else None
    if not isinstance(sections, list) or not sections:
        raise AIProviderError("Provider output did not contain insight sections.")
    cleaned = []
    for section in sections:
        if not isinstance(section, dict):
            raise AIProviderError("Insight section was malformed.")
        if not section.get("type") or not section.get("title") or not section.get("content"):
            raise AIProviderError("Insight section was missing required fields.")
        cleaned.append(
            {
                "type": str(section["type"]),
                "title": str(section["title"]),
                "content": str(section["content"]),
            }
        )
    return {"sections": cleaned}
