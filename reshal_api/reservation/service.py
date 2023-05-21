import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.base import BaseCRUDService

from .models import Reservation
from .schemas import ReservationCreate, ReservationUpdate


class ReservationService(
    BaseCRUDService[Reservation, ReservationCreate, ReservationUpdate]
):
    def __init__(self) -> None:
        super().__init__(Reservation)

    async def is_overlapping(
        self,
        session: AsyncSession,
        facility_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        q = (
            select(Reservation)
            .filter(Reservation.facility_id == facility_id)
            .filter(Reservation.start_time < end_time)
            .filter(Reservation.end_time > start_time)
        )
        result = (await session.execute(q)).scalar_one_or_none()
        return bool(result)

    async def get_all_in_timeframe(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        *args,
        **kwargs
    ) -> Sequence[Reservation]:
        q = (
            select(Reservation)
            .filter(Reservation.start_time >= start_time)
            .filter(Reservation.end_time <= end_time)
        )

        reservations = (
            (await session.execute(q.filter(*args).filter_by(**kwargs))).scalars().all()
        )
        return reservations
