import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import insert

from reshal_api.base import BaseCRUDService

from .exceptions import InvalidAuthRequest
from .models import User
from .schemas import AuthRequest, UserCreate, UserUpdate
from .security import hash_password, is_valid_password


class AuthService(BaseCRUDService[User, UserCreate, UserUpdate]):
    def __init__(self) -> None:
        super().__init__(User)

    async def create(self, session: AsyncSession, create_obj: UserCreate) -> User:
        create_obj.password = hash_password(create_obj.password)
        return await super().create(session, create_obj)

    async def update(
        self,
        session: AsyncSession,
        *,
        update_obj: UserUpdate | dict[str, Any],
        db_obj: User | None = None,
        **kwargs
    ) -> User:
        if isinstance(update_obj, UserUpdate):
            update_obj = update_obj.dict(exclude_unset=True)

        if update_obj.get("new_password"):
            update_obj["password"] = hash_password(update_obj["new_password"])

        return await super().update(
            session, update_obj=update_obj, db_obj=db_obj, **kwargs
        )

    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        result = await self.get(session, email=email)
        return result

    async def get_by_id(self, session: AsyncSession, id: uuid.UUID) -> Optional[User]:
        result = await self.get(session, id=id)
        return result

    async def is_password_valid(self, user: User, password: str) -> bool:
        return is_valid_password(password, user.password)

    async def authenticate_user(self, session: AsyncSession, data: AuthRequest) -> User:
        user = await self.get_by_email(session, data.email)
        if user is None:
            raise InvalidAuthRequest()

        if not is_valid_password(data.password, user.password):
            raise InvalidAuthRequest()

        return user

    async def create_superuser(self, session: AsyncSession, data: UserCreate) -> User:
        data.password = hash_password(data.password)
        user = (
            await session.execute(
                insert(User).values(**data.dict(), is_superuser=True).returning(User)
            )
        ).scalar()
        await session.commit()
        return user
