from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.auth.dependencies import get_admin, get_db_session, get_user
from reshal_api.auth.models import User, UserRole
from reshal_api.exceptions import Forbidden, NotFound
from reshal_api.reservation.dependencies import get_reservation_service
from reshal_api.reservation.service import ReservationService

from .dependencies import get_payment_service, valid_payment
from .models import Payment
from .schemas import PaymentRead
from .service import PaymentService

router = APIRouter(tags=["payment"])


@router.get("", response_model=list[PaymentRead], dependencies=[Depends(get_admin)])
async def get_payments(
    session: AsyncSession = Depends(get_db_session),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payments = await payment_service.get_all(session)
    return payments


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment_by_id(
    payment_id: str,
    session: AsyncSession = Depends(get_db_session),
    payment: Payment = Depends(valid_payment),
    user: User = Depends(get_user),
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    reservation = await reservation_service.get(session, id=payment.reservation_id)
    if reservation is None:
        raise NotFound()

    if not (reservation.user_id == user.id or user.role == UserRole.admin):
        raise Forbidden()
    return payment
