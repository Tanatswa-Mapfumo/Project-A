"""Weekly summary model (Phase 2)."""

import datetime as dt
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, jsonb_column


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_weekly_summaries_user_week"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"), nullable=False)
    week_start: Mapped[dt.date] = mapped_column(Date, nullable=False)
    week_end: Mapped[dt.date] = mapped_column(Date, nullable=False)
    consistency_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    recovery_notes: Mapped[str] = mapped_column(Text, nullable=False)
    progression_notes: Mapped[str] = mapped_column(Text, nullable=False)
    planned_adjustments: Mapped[dict] = mapped_column(jsonb_column(), nullable=False, default=dict)
    metrics: Mapped[dict] = mapped_column(jsonb_column(), nullable=False, default=dict)
    deep_insight: Mapped[dict | None] = mapped_column(jsonb_column())
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.UTC)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.UTC),
        onupdate=lambda: dt.datetime.now(dt.UTC),
    )
