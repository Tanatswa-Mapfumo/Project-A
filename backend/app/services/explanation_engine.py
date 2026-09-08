"""AI explanation engine (sections 16-17).

Generates short explanations and Deep Insight from the rule_trace only. Never
fails workout generation: on any provider/validation failure the deterministic
template fallback is used (section 16.3).
"""

from app.ai.base import (
    AIProviderError,
    get_mock_provider,
    get_provider,
    log_provider_failure,
)
from app.ai.mock import build_short_explanation
from app.core.exceptions import AppError, ErrorCode
from app.core.logging import get_logger
from app.db.models.workout import WorkoutPlan
from app.repositories.workouts import WorkoutRepository
from app.rules.config import BANNED_MEDICAL_TERMS, SHORT_EXPLANATION_MAX_CHARS

logger = get_logger("app.explanations")


def validate_short_explanation(
    text: str,
    plan_names: list[str],
    other_names: list[str],
) -> list[str]:
    """Conservative string/fact checks (section 16.4)."""
    errors: list[str] = []
    if not text or not text.strip():
        return ["Explanation is empty."]
    if len(text) > SHORT_EXPLANATION_MAX_CHARS:
        errors.append("Explanation is too long.")
    lowered = text.lower()
    for term in BANNED_MEDICAL_TERMS:
        if term in lowered:
            errors.append(f"Explanation contains disallowed language: {term}")
            break
    for name in other_names:
        if name and name.lower() in lowered:
            errors.append(f"Explanation mentions an exercise not in the plan: {name}")
            break
    return errors


def plan_summary(plan: WorkoutPlan) -> dict:
    return {
        "type": plan.type,
        "intensity": plan.intensity,
        "duration_minutes": plan.duration_minutes,
        "goal_tags": list(plan.goal_tags or []),
    }


class ExplanationEngine:
    def __init__(self, session) -> None:
        self.session = session
        self.workouts = WorkoutRepository(session)

    async def generate_and_persist_short(
        self,
        plan: WorkoutPlan,
        source_facts: dict,
        plan_names: list[str],
        other_names: list[str],
    ) -> str:
        try:
            provider = get_provider()
        except AIProviderError as exc:
            log_provider_failure("provider_init", exc)
            provider = get_mock_provider()
        text = await self._try_short(provider, plan, source_facts, plan_names, other_names)
        explanation = await self.workouts.upsert_explanation(
            plan.id,
            provider=provider.name,
            model=provider.model,
            short_text=text,
            source_facts=source_facts,
        )
        plan.short_explanation = explanation.short_text
        return text

    async def _try_short(self, provider, plan, source_facts, plan_names, other_names) -> str:
        try:
            text = await provider.generate_short_explanation(source_facts, _plan_facts(plan))
            errors = validate_short_explanation(text, plan_names, other_names)
            if not errors:
                return text.strip()
            logger.warning("explanation_rejected plan=%s errors=%s", plan.id, errors)
        except (AIProviderError, AppError) as exc:
            log_provider_failure("short_explanation", exc)
        return build_short_explanation(source_facts)

    async def get_or_generate_deep_insight(
        self,
        plan: WorkoutPlan,
        source_facts: dict,
        history_summary: dict,
    ) -> dict:
        explanation = await self.workouts.get_explanation(plan.id)
        if explanation is not None and explanation.deep_insight:
            return explanation.deep_insight
        try:
            provider = get_provider()
            sections = await provider.generate_deep_insight(
                source_facts, _plan_facts(plan), history_summary
            )
        except (AIProviderError, AppError) as exc:
            log_provider_failure("deep_insight", exc)
            raise AppError(
                503,
                ErrorCode.AI_INSIGHT_UNAVAILABLE,
                "The AI insight service is currently unavailable.",
            ) from exc
        if explanation is None:
            explanation = await self.workouts.upsert_explanation(
                plan.id,
                provider=provider.name,
                model=provider.model,
                short_text=build_short_explanation(source_facts),
                source_facts=source_facts,
            )
        await self.workouts.save_deep_insight(explanation, sections)
        await self.session.commit()
        return sections


def _plan_facts(plan: WorkoutPlan) -> dict:
    return {
        "id": str(plan.id),
        "plan_date": plan.plan_date.isoformat(),
        "type": plan.type,
        "intensity": plan.intensity,
        "duration_minutes": plan.duration_minutes,
        "goal_tags": list(plan.goal_tags or []),
    }
