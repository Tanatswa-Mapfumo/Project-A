"""Prompt templates for the explanation engine (section 16.2).

Every prompt forces the model to use only supplied facts and forbids inventing
measurements, medical claims, conditions, or new exercises.
"""

SYSTEM_PROMPT = (
    "You are a warm, supportive fitness coach assistant. You explain workout plans that were "
    "already created by a deterministic rules engine. You MUST only use the structured facts "
    "provided to you. Never invent measurements, never invent medical claims, never claim the "
    "user has a condition, never introduce exercises that are not in the supplied plan, and "
    "never tell a user to train through pain. Be transparent about the main adaptation reason."
)

SHORT_EXPLANATION_PROMPT = """{system_prompt}

Structured facts:
{source_facts}

Workout plan:
{workout_plan}

Write exactly ONE sentence explaining why today's workout was adapted this way.
Keep it warm and coach-like. Do not add anything that is not in the facts."""

DEEP_INSIGHT_PROMPT = """{system_prompt}

Structured facts:
{source_facts}

Workout plan:
{workout_plan}

Recent history summary:
{history_summary}

Return STRICT JSON with this exact shape:
{{"sections": [
  {{"type": "recovery", "title": "Recovery Insight", "content": "..."}},
  {{"type": "energy", "title": "Energy Trend", "content": "..."}},
  {{"type": "soreness", "title": "Soreness Analysis", "content": "..."}},
  {{"type": "burnout", "title": "Burnout Risk", "content": "..."}},
  {{"type": "progression", "title": "Long-Term Progression Impact", "content": "..."}}
]}}
Every content string must be derived only from the supplied facts."""

WEEKLY_INSIGHT_PROMPT = """{system_prompt}

Weekly aggregate facts:
{week_facts}

Return STRICT JSON with this exact shape:
{{"sections": [
  {{"type": "consistency", "title": "Consistency", "content": "..."}},
  {{"type": "recovery", "title": "Recovery Pattern", "content": "..."}},
  {{"type": "energy", "title": "Energy Trend", "content": "..."}},
  {{"type": "adjustment", "title": "Next Week Plan", "content": "..."}}
]}}
Every content string must be derived only from the supplied facts."""
