from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.dependencies import get_admin, get_db_session, get_user
from reshal_api.auth.models import User, UserRole
from reshal_api.exceptions import Conflict, Forbidden, NotFound
from reshal_api.facility.dependencies import facility_exists, get_facility_service
from reshal_api.facility.models import Facility
from reshal_api.facility.service import FacilityService

from .dependencies import get_timeframe_service, valid_timeframe
from .models import TimeFrame
from .schemas import TimeFrameCreate, TimeFrameReadBase
from .service import TimeFrameService

router = APIRouter(tags=["timeframe"])


@router.get(
    "", response_model=list[TimeFrameReadBase], dependencies=[Depends(get_admin)]
)
async def get_timeframes(
    session: AsyncSession = Depends(get_db_session),
    timeframe_service: TimeFrameService = Depends(get_timeframe_service),
):
    timeframes = await timeframe_service.get_all(session)
    return timeframes


@router.get("/{facility_id}", response_model=list[TimeFrameReadBase])
async def get_timeframes_for_facility(
    facility_id: str,
    session: AsyncSession = Depends(get_db_session),
    facility: Facility = Depends(facility_exists),
    timeframe_service: TimeFrameService = Depends(get_timeframe_service),
):
    return await timeframe_service.get_all(session, facility_id=facility_id)


@router.post("", response_model=TimeFrameReadBase)
async def create_timeframe(
    data: TimeFrameCreate,
    session: AsyncSession = Depends(get_db_session),
    timeframe_service: TimeFrameService = Depends(get_timeframe_service),
    facility_service: FacilityService = Depends(get_facility_service),
    user: User = Depends(get_user),
):
    facility = await facility_service.get(session, id=data.facility_id)
    if facility is None:
        raise NotFound("Facility not found")

    if not (facility.is_owner(user.id) or user.role == UserRole.admin):
        raise Forbidden()

    timeframe_same_duration = await timeframe_service.get(
        session, duration=data.duration
    )
    if timeframe_same_duration is not None:
        raise Conflict("Timeframe with same duration already exists")

    timeframe = await timeframe_service.create(session, data.dict())
    await session.refresh(timeframe, ["facility"])
    return timeframe


# TODO: validate if timeframe is in use
@router.delete("/{timeframe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_timeframe(
    timeframe_id: str,
    session: AsyncSession = Depends(get_db_session),
    timeframe_service: TimeFrameService = Depends(get_timeframe_service),
    timeframe: TimeFrame = Depends(valid_timeframe),
    user: User = Depends(get_user),
):
    await session.refresh(timeframe, ["facility"])
    if not (timeframe.facility.is_owner(user.id) or user.role == UserRole.admin):
        raise Forbidden()

    await timeframe_service.delete(session, db_obj=timeframe)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
