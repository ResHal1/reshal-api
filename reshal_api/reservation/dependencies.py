from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.dependencies import get_db_session
from reshal_api.exceptions import NotFound

from .service import ReservationService


async def get_reservation_service() -> ReservationService:
    return ReservationService()


async def valid_reservation(
    reservation_id: str,
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    reservation = await reservation_service.get(session, id=reservation_id)
    if reservation is None:
        raise NotFound("Reservation not found")
    return reservation
