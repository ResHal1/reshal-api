import uuid
from typing import Optional

from reshal_api.base import ORJSONBaseModel

from .models import PaymentStatus


class PaymentBase(ORJSONBaseModel):
    reservation_id: Optional[uuid.UUID]
    price: float


class PaymentRead(PaymentBase):
    id: uuid.UUID
    status: PaymentStatus

    class Config:
        orm_mode = True


class PaymentCreate(PaymentBase):
    ...


class PaymentUpdate(PaymentBase):
    status: PaymentStatus
