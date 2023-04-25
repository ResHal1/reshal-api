import uuid

from sqlalchemy.orm import Mapped, mapped_column

from reshal_api.database import Base
from reshal_api.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str] = mapped_column()
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    is_superuser: Mapped[bool] = mapped_column(default=False)
