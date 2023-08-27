from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api.database import get_db_session

from .exceptions import UserIsNotSuperuser, UserNotFound, UserRoleNotSufficient
from .jwt import get_data_from_token
from .models import User, UserRole
from .schemas import JWTData
from .service import AuthService


async def get_auth_service() -> AuthService:
    return AuthService()


async def get_user(
    jwt_data: JWTData = Depends(get_data_from_token),
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    user = await auth_service.get_by_id(session, jwt_data.user_id)
    if user is None:
        raise UserNotFound()
    return user


async def get_owner(user: User = Depends(get_user)) -> User:
    if user.role not in (UserRole.owner, UserRole.admin):
        raise UserRoleNotSufficient("Not an owner")
    return user


async def get_admin(user: User = Depends(get_user)) -> User:
    if user.role != UserRole.admin:
        raise UserIsNotSuperuser()
    return user
