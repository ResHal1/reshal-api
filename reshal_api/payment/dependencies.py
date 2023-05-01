from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.database import get_db_session
from reshal_api.exceptions import NotFound

from .service import PaymentService


async def get_payment_service():
    return PaymentService()


async def valid_payment(
    payment_id: str,
    session: AsyncSession = Depends(get_db_session),
    payment_service: PaymentService = Depends(get_payment_service),
):
    payment = await payment_service.get(session, id=payment_id)
    if payment is None:
        raise NotFound("Payment not found")
    return payment
