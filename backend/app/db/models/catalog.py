"""Catalog models: equipment, user_equipment, exercises, exercise_equipment."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, jsonb_column


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UserEquipment(Base):
    __tablename__ = "user_equipment"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"), primary_key=True)
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("equipment.id"), primary_key=True
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    workout_type: Mapped[str] = mapped_column(String, nullable=False)
    movement_pattern: Mapped[str] = mapped_column(String, nullable=False)
    primary_muscle_groups: Mapped[list] = mapped_column(
        jsonb_column(), nullable=False, default=list
    )
    secondary_muscle_groups: Mapped[list] = mapped_column(
        jsonb_column(), nullable=False, default=list
    )
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    is_unilateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta: Mapped[dict] = mapped_column("metadata", jsonb_column(), nullable=False, default=dict)

    equipment_items: Mapped[list[Equipment]] = relationship(
        "Equipment", secondary="exercise_equipment", lazy="selectin"
    )


class ExerciseEquipment(Base):
    __tablename__ = "exercise_equipment"

    exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exercises.id"), primary_key=True
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("equipment.id"), primary_key=True
    )
