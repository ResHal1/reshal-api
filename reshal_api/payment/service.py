from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.base import BaseCRUDService

from .models import Payment, PaymentStatus
from .schemas import PaymentCreate, PaymentUpdate


class PaymentService(BaseCRUDService[Payment, PaymentCreate, PaymentUpdate]):
    def __init__(self) -> None:
        super().__init__(Payment)

    async def create_payment(self, session: AsyncSession, create_obj: PaymentCreate):
        create_obj_dict = create_obj.dict()
        create_obj_dict["status"] = PaymentStatus.paid
        payment = await self.create(session, create_obj_dict)
        return payment

    async def set_status(self, db_obj: Payment, new_status: PaymentStatus) -> None:
        if db_obj.status == new_status:
            raise ValueError("Old and new status is the same")
        if new_status == PaymentStatus.paid:
            if db_obj.reservation_id is None:
                raise ValueError(
                    "Cannot set payment status to 'paid' if payment is not assigned to reservation"
                )
            if db_obj.status in (PaymentStatus.cancelled, PaymentStatus.failed):
                raise ValueError(
                    f"Cannot change status from {db_obj.status.value!r} to 'paid'"
                )

        db_obj.status = new_status
