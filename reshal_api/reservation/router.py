from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.dependencies import get_admin, get_user
from reshal_api.auth.models import User, UserRole
from reshal_api.base import DatetimeQuery
from reshal_api.database import get_db_session
from reshal_api.email import tasks as email_tasks
from reshal_api.email.dependencies import EmailService, TemplatesService
from reshal_api.exceptions import Conflict, Forbidden, NotFound
from reshal_api.facility.dependencies import get_facility_service
from reshal_api.facility.service import FacilityService
from reshal_api.payment.dependencies import get_payment_service
from reshal_api.payment.schemas import PaymentCreate
from reshal_api.payment.service import PaymentService

# from reshal_api.timeframe.dependencies import get_timeframe_service
# from reshal_api.timeframe.service import TimeFrameService
from .dependencies import get_reservation_service, valid_reservation
from .models import Reservation
from .schemas import (
    ReservationCreate,
    ReservationCreateBase,
    ReservationRead,
    ReservationReadBase,
)
from .service import ReservationService

router = APIRouter(tags=["reservation"])


@router.get(
    "", response_model=list[ReservationReadBase], dependencies=[Depends(get_admin)]
)
async def get_all_reservations(
    # startTime: Annotated[datetime, DatetimeQuery()] = datetime.now(),
    # endTime: Annotated[datetime, DatetimeQuery()] = datetime.now() + timedelta(weeks=4),
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    # reservations = await reservation_service.get_all_in_timeframe(
    #     session, startTime, endTime
    # )
    reservations = await reservation_service.get_all(
        session, Reservation.facility_id != None  # noqa: E711
    )
    return reservations


@router.get("/me", response_model=list[ReservationReadBase])
async def get_reservations_me(
    startTime: Annotated[datetime, DatetimeQuery()] = datetime.now(),
    endTime: Annotated[datetime, DatetimeQuery()] = datetime.now() + timedelta(weeks=4),
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_user),
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    user_reservations = await reservation_service.get_all_in_timeframe(
        session, startTime, endTime, user_id=user.id
    )
    return user_reservations


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ReservationRead,
)
async def create_reservation(
    data: ReservationCreateBase,
    email_service: EmailService,
    templates_service: TemplatesService,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
    facility_service: FacilityService = Depends(get_facility_service),
    # timeframe_service: TimeFrameService = Depends(get_timeframe_service),
    payment_service: PaymentService = Depends(get_payment_service),
    user: User = Depends(get_user),
):
    # timeframe = await timeframe_service.get(
    #     session, id=data.timeframe_id, facility_id=data.facility_id
    # )
    # if timeframe is None:
    #     raise NotFound("Timeframe not found")

    # end_time = data.start_time + timedelta(seconds=timeframe.duration)
    facility = await facility_service.get(session, id=data.facility_id)

    if facility is None:
        raise NotFound()

    if await reservation_service.is_overlapping(
        session,
        data.facility_id,
        data.start_time,
        data.end_time,
    ):
        raise Conflict("Reservation overlaps with another reservation")

    reservation_price = reservation_service.calcualte_price(
        facility.price, data.start_time, data.end_time
    )

    payment = await payment_service.create_payment(
        session, create_obj=PaymentCreate(reservation_id=None, price=reservation_price)
    )
    await session.flush()

    create_obj = ReservationCreate(
        **data.dict(),
        price=reservation_price,
        payment_id=payment.id,
        user_id=user.id,
    )
    reservation = await reservation_service.create(session, create_obj)
    payment.reservation_id = reservation.id

    background_tasks.add_task(
        email_tasks.send_reservation_confirmation,
        email_service,
        templates_service,
        user.email,
        user.first_name,
        facility.name,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        price=reservation.price,
    )

    return reservation


@router.get("/{reservation_id}", response_model=ReservationRead)
async def get_reservation_by_id(
    reservation_id: str,
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
    reservation: Reservation = Depends(valid_reservation),
    user: User = Depends(get_user),
):
    if not (
        reservation.user_id == user.id
        or reservation.facility.is_owner(user.id)
        or user.role == UserRole.admin
    ):
        raise Forbidden()
    return reservation


# FIXME: ADMIN
@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: str,
    user: User = Depends(get_user),
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    reservation = await reservation_service.get(session, id=reservation_id)
    if reservation and (user.role == UserRole.admin or reservation.user_id == user.id):
        await reservation_service.delete(session, db_obj=reservation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
