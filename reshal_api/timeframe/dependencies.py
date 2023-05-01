from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.dependencies import get_db_session
from reshal_api.exceptions import NotFound

from .service import TimeFrameService


async def get_timeframe_service() -> TimeFrameService:
    return TimeFrameService()


async def valid_timeframe(
    timeframe_id: str,
    session: AsyncSession = Depends(get_db_session),
    timeframe_service: TimeFrameService = Depends(get_timeframe_service),
):
    timeframe = await timeframe_service.get(session, id=timeframe_id)
    if timeframe is None:
        raise NotFound("Reservation timeframe not found")
    return timeframe
