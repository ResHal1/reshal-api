import uuid
from enum import Enum

from sqlalchemy.orm import Mapped, mapped_column, relationship

from reshal_api.database import Base
from reshal_api.facility.models import Facility
from reshal_api.mixins import TimestampMixin


class UserRole(str, Enum):
    admin = "admin"
    owner = "owner"
    normal = "normal"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str] = mapped_column()
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    role: Mapped[UserRole] = mapped_column(default="normal")

    facilities: Mapped[list[Facility]] = relationship(
        secondary="facility_owners",
        back_populates="owners",
        lazy="raise",
    )

    async def set_is_owner(self):
        self.is_owner = bool(self.facilities)
