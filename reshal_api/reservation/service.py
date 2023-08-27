import math
import uuid
from datetime import datetime
from decimal import Decimal
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

    def calcualte_price(
        self,
        facility_price_per_hour: Decimal,
        start_time: datetime,
        end_time: datetime,
    ) -> Decimal:
        """
        Calculate the price of the facility for the given time range
        Rounds up the hours to the next integer if the time range is not a whole hour
        """
        hours = math.ceil((end_time - start_time).total_seconds() / 3600)
        total_price = hours * facility_price_per_hour
        return total_price
