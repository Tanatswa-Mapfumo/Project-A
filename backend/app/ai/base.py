"""AI provider abstraction.

The LLM is for language generation only: it explains structured facts already
produced by the deterministic engine. It never plans workouts, writes to the
database, or invents metrics.
"""

from typing import Protocol, runtime_checkable

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("app.ai")


class AIProviderError(Exception):
    """Raised when the provider is unreachable, times out, or returns invalid output."""


@runtime_checkable
class AIProvider(Protocol):
    name: str
    model: str

    async def generate_short_explanation(self, source_facts: dict, workout_plan: dict) -> str: ...

    async def generate_deep_insight(
        self,
        source_facts: dict,
        workout_plan: dict,
        history_summary: dict,
    ) -> dict: ...

    async def generate_weekly_insight(self, week_facts: dict) -> dict: ...


def get_provider() -> AIProvider:
    if settings.ai_provider == "gemini":
        from app.ai.gemini import GeminiAIProvider

        return GeminiAIProvider()
    return get_mock_provider()


def get_mock_provider() -> AIProvider:
    from app.ai.mock import MockAIProvider

    return MockAIProvider()


def log_provider_failure(operation: str, exc: Exception) -> None:
    logger.warning("ai_provider_failure operation=%s category=%s", operation, type(exc).__name__)
