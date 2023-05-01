import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reshal_api.database import Base
from reshal_api.mixins import TimestampMixin

if TYPE_CHECKING:
    from reshal_api.facility.models import Facility


class TimeFrame(Base, TimestampMixin):
    __tablename__ = "timeframe"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facility.id", ondelete="CASCADE"), primary_key=True
    )
    duration: Mapped[int] = mapped_column()
    price: Mapped[float] = mapped_column()

    facility: Mapped["Facility"] = relationship(
        back_populates="timeframes", lazy="raise"
    )
