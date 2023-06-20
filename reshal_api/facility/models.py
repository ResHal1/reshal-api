import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, ForeignKey, Numeric, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reshal_api.database import Base
from reshal_api.mixins import TimestampMixin

if TYPE_CHECKING:
    from reshal_api.auth.models import User
    from reshal_api.reservation.models import Reservation
    from reshal_api.timeframe.models import TimeFrame


class FacilityImage(Base, TimestampMixin):
    __tablename__ = "facility_image"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facility.id", ondelete="CASCADE"), nullable=True
    )
    path: Mapped[str] = mapped_column()


assoc_facility_owners = Table(
    "facility_owners",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "facility_id", ForeignKey("facility.id", ondelete="CASCADE"), primary_key=True
    ),
)


class FacilityType(Base, TimestampMixin):
    __tablename__ = "facility_type"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(length=80))

    facilities: Mapped["Facility"] = relationship(back_populates="type", lazy="raise")


class Facility(TimestampMixin, Base):
    __tablename__ = "facility"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column()
    lat: Mapped[Decimal] = mapped_column(Numeric(10, 8))
    lon: Mapped[Decimal] = mapped_column(Numeric(11, 8))
    image_url: Mapped[str] = mapped_column()
    address: Mapped[str] = mapped_column()
    type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facility_type.id", ondelete="RESTRICT")
    )

    type: Mapped[FacilityType] = relationship(
        back_populates="facilities", lazy="selectin"
    )
    owners: Mapped[list["User"]] = relationship(
        secondary=assoc_facility_owners, lazy="selectin"
    )
    # images: Mapped[list[FacilityImage]] = relationship(lazy="selectin")

    timeframes: Mapped[list["TimeFrame"]] = relationship(
        back_populates="facility", lazy="raise"
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="facility", lazy="raise"
    )

    def is_owner(self, user_id: uuid.UUID) -> bool:
        return any(user_id == owner.id for owner in self.owners)
