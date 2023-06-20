import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reshal_api.database import Base
from reshal_api.mixins import TimestampMixin
from reshal_api.payment.models import Payment

if TYPE_CHECKING:
    from reshal_api.facility.models import Facility


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservation"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facility.id", ondelete="SET NULL"),
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    # timeframe_id: Mapped[uuid.UUID] = mapped_column(
    #     ForeignKey("timeframe.id", ondelete="SET NULL")
    # )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment.id", ondelete="SET NULL")
    )

    facility: Mapped["Facility"] = relationship(
        back_populates="reservations", lazy="selectin"
    )
    payment: Mapped[Payment] = relationship(foreign_keys=[payment_id], lazy="selectin")
