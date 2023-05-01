from datetime import timedelta

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.dependencies import get_admin, get_user
from reshal_api.auth.models import User, UserRole
from reshal_api.database import get_db_session
from reshal_api.exceptions import Conflict, Forbidden, NotFound
from reshal_api.payment.dependencies import get_payment_service
from reshal_api.payment.schemas import PaymentCreate
from reshal_api.payment.service import PaymentService
from reshal_api.timeframe.dependencies import get_timeframe_service
from reshal_api.timeframe.service import TimeFrameService

from .dependencies import get_reservation_service, valid_reservation
from .models import Reservation
from .schemas import ReservationCreate, ReservationCreateBase, ReservationReadBase
from .service import ReservationService

router = APIRouter(tags=["reservation"])

# TODO: public reservations endpoint


@router.get(
    "/", response_model=list[ReservationReadBase], dependencies=[Depends(get_admin)]
)
async def get_all_reservations(
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    reservations = await reservation_service.get_all(session)
    return reservations


@router.post("/")
async def create_reservation(
    data: ReservationCreateBase,
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
    timeframe_service: TimeFrameService = Depends(get_timeframe_service),
    payment_service: PaymentService = Depends(get_payment_service),
    user: User = Depends(get_user),
):
    timeframe = await timeframe_service.get(
        session, id=data.timeframe_id, facility_id=data.facility_id
    )
    if timeframe is None:
        raise NotFound("Timeframe not found")

    end_time = data.start_time + timedelta(seconds=timeframe.duration)

    if await reservation_service.is_overlapping(
        session, data.facility_id, data.start_time, end_time
    ):
        raise Conflict("Reservation overlaps with another reservation")

    payment = await payment_service.create_payment(
        session, create_obj=PaymentCreate(reservation_id=None, price=timeframe.price)
    )
    await session.flush()

    create_obj = ReservationCreate(
        **data.dict(), payment_id=payment.id, user_id=user.id, end_time=end_time
    )
    reservation = await reservation_service.create(session, create_obj)
    payment.reservation_id = reservation.id
    return reservation


@router.get("/{reservation_id}")
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


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: str,
    user: User = Depends(get_user),
    session: AsyncSession = Depends(get_db_session),
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    reservation = await reservation_service.get(session, id=reservation_id)
    if reservation and reservation.user_id == user.id:
        await reservation_service.delete(session, db_obj=reservation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)