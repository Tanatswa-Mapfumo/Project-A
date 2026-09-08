"""Check-in repository."""

import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.checkin import CheckIn


class CheckInRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        checkin_date: dt.date,
        values: dict,
    ) -> CheckIn:
        check_in = CheckIn(user_id=user_id, checkin_date=checkin_date, **values)
        self.session.add(check_in)
        await self.session.flush()
        return check_in

    async def get(self, user_id: uuid.UUID, check_in_id: uuid.UUID) -> CheckIn | None:
        result = await self.session.execute(
            select(CheckIn).where(CheckIn.id == check_in_id, CheckIn.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_for_date(self, user_id: uuid.UUID, checkin_date: dt.date) -> CheckIn | None:
        result = await self.session.execute(
            select(CheckIn).where(CheckIn.user_id == user_id, CheckIn.checkin_date == checkin_date)
        )
        return result.scalar_one_or_none()

    async def paginate(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[CheckIn], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(CheckIn).where(CheckIn.user_id == user_id)
        )
        result = await self.session.execute(
            select(CheckIn)
            .where(CheckIn.user_id == user_id)
            .order_by(CheckIn.checkin_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_in_range(
        self, user_id: uuid.UUID, start: dt.date, end: dt.date
    ) -> list[CheckIn]:
        result = await self.session.execute(
            select(CheckIn)
            .where(
                CheckIn.user_id == user_id,
                CheckIn.checkin_date >= start,
                CheckIn.checkin_date <= end,
            )
            .order_by(CheckIn.checkin_date.asc())
        )
        return list(result.scalars().all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        return int(
            await self.session.scalar(
                select(func.count()).select_from(CheckIn).where(CheckIn.user_id == user_id)
            )
            or 0
        )
