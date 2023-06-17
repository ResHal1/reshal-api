from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from reshal_api import exceptions
from reshal_api.config import get_config
from reshal_api.database import get_db_session

from .dependencies import get_admin, get_auth_service, get_user
from .exceptions import EmailAlreadyExists
from .jwt import create_access_token
from .models import User
from .schemas import AccessTokenResponse, AuthRequest, UserCreate, UserRead, UserUpdate
from .service import AuthService

config = get_config()
router = APIRouter(tags=["auth"])


@router.get("/", response_model=list[UserRead], dependencies=[Depends(get_admin)])
async def get_users(
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
):
    users = await auth_service.get_all(session)
    return users


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserRead)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
):
    email_exists = bool(await auth_service.get_by_email(session, data.email))
    if email_exists:
        raise EmailAlreadyExists()

    user = await auth_service.create(session, data)
    return user


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_user)):
    return user


@router.put("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
    user: User = Depends(get_user),
):
    if not (await auth_service.is_password_valid(user, data.current_password)):
        raise exceptions.Forbidden("Invalid password")

    if data.email and data.email != user.email:
        email_exists = bool(await auth_service.get_by_email(session, data.email))
        if email_exists:
            raise EmailAlreadyExists()

    updated_user = await auth_service.update(session, db_obj=user, update_obj=data)
    return updated_user


@router.post("/token", response_model=AccessTokenResponse)
async def auth_user(
    data: AuthRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.authenticate_user(session, data)
    access_token = create_access_token(user)

    response.set_cookie(
        config.ACCESS_TOKEN_COOKIE_NAME,
        f"Bearer {access_token}",
        max_age=config.ACCESS_TOKEN_EXPIRE * 60,
        samesite="none",
        httponly=True,
        secure=config.ENVIRONMENT.is_production,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_user)]
)
async def logout(response: Response):
    response.delete_cookie(
        config.ACCESS_TOKEN_COOKIE_NAME,
        httponly=True,
        samesite="none",
        secure=config.ENVIRONMENT.is_production,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
