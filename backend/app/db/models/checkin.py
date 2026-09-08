"""Daily check-in model."""

import datetime as dt
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, Integer, SmallInteger, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, jsonb_column


class CheckIn(Base):
    __tablename__ = "check_ins"
    __table_args__ = (UniqueConstraint("user_id", "checkin_date", name="uq_check_ins_user_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"), nullable=False)
    checkin_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    energy_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    soreness_map: Mapped[dict] = mapped_column(jsonb_column(), nullable=False, default=dict)
    mood_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    sleep_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    stress_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    time_available_minutes: Mapped[int | None] = mapped_column(Integer)
    pain_score: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.UTC)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.UTC),
        onupdate=lambda: dt.datetime.now(dt.UTC),
    )
