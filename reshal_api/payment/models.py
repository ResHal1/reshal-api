import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from reshal_api.database import Base
from reshal_api.mixins import TimestampMixin


class PaymentStatus(Enum):
    paid = "paid"
    pending = "pending"
    cancelled = "cancelled"
    failed = "failed"


class Payment(Base, TimestampMixin):
    __tablename__ = "payment"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reservation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("reservation.id", ondelete="SET NULL")
    )
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.pending)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 0))
