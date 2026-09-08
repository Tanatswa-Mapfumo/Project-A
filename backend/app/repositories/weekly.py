"""Weekly summary repository."""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.weekly import WeeklySummary


class WeeklyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID, week_start: dt.date) -> WeeklySummary | None:
        result = await self.session.execute(
            select(WeeklySummary).where(
                WeeklySummary.user_id == user_id, WeeklySummary.week_start == week_start
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        week_start: dt.date,
        week_end: dt.date,
        consistency_score: float,
        recovery_notes: str,
        progression_notes: str,
        planned_adjustments: dict,
        metrics: dict,
    ) -> WeeklySummary:
        summary = await self.get(user_id, week_start)
        if summary is None:
            summary = WeeklySummary(
                user_id=user_id,
                week_start=week_start,
                week_end=week_end,
                consistency_score=consistency_score,
                recovery_notes=recovery_notes,
                progression_notes=progression_notes,
                planned_adjustments=planned_adjustments,
                metrics=metrics,
            )
            self.session.add(summary)
        else:
            summary.week_end = week_end
            summary.consistency_score = consistency_score
            summary.recovery_notes = recovery_notes
            summary.progression_notes = progression_notes
            summary.planned_adjustments = planned_adjustments
            summary.metrics = metrics
        await self.session.flush()
        return summary

    async def save_deep_insight(self, summary: WeeklySummary, sections: dict) -> None:
        summary.deep_insight = sections
        await self.session.flush()
