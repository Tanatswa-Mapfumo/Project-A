"""Gemini-compatible AI provider adapter."""

import json

import httpx

from app.ai.base import AIProviderError
from app.ai.prompts import (
    DEEP_INSIGHT_PROMPT,
    SHORT_EXPLANATION_PROMPT,
    SYSTEM_PROMPT,
    WEEKLY_INSIGHT_PROMPT,
)
from app.config import settings

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiAIProvider:
    name = "gemini"
    model = settings.ai_model

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise AIProviderError("GEMINI_API_KEY is not configured.")

    async def _generate(self, prompt: str) -> str:
        url = GEMINI_ENDPOINT.format(model=self.model)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3},
        }
        try:
            async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
                resp = await client.post(url, params={"key": settings.gemini_api_key}, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise AIProviderError("Gemini request timed out.") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError("Gemini request failed.") from exc
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("Gemini returned an unexpected response shape.") from exc

    async def generate_short_explanation(self, source_facts: dict, workout_plan: dict) -> str:
        prompt = SHORT_EXPLANATION_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            source_facts=json.dumps(source_facts),
            workout_plan=json.dumps(workout_plan),
        )
        text = await self._generate(prompt)
        text = text.strip().strip('"')
        if not text:
            raise AIProviderError("Gemini returned an empty explanation.")
        return text

    async def generate_deep_insight(
        self,
        source_facts: dict,
        workout_plan: dict,
        history_summary: dict,
    ) -> dict:
        prompt = DEEP_INSIGHT_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            source_facts=json.dumps(source_facts),
            workout_plan=json.dumps(workout_plan),
            history_summary=json.dumps(history_summary),
        )
        raw = await self._generate(prompt)
        from app.ai.mock import parse_json_sections

        return parse_json_sections(raw)

    async def generate_weekly_insight(self, week_facts: dict) -> dict:
        prompt = WEEKLY_INSIGHT_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            week_facts=json.dumps(week_facts),
        )
        raw = await self._generate(prompt)
        from app.ai.mock import parse_json_sections

        return parse_json_sections(raw)
