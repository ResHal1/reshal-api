from datetime import datetime, timedelta
from typing import Annotated, Optional, cast

from fastapi import Depends, Header
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt

from reshal_api.config import get_config

from .exceptions import InvalidToken
from .models import User
from .schemas import JWTData
from .security import OAuth2PasswordBearerCookie

config = get_config()

oauth2_scheme = OAuth2PasswordBearerCookie(token_url="/auth/token", auto_error=False)


def create_access_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE)
    return jwt.encode(
        {"exp": expire, "user_id": str(user.id), "role": user.role},
        key=config.SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def get_data_from_token(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    cookie_token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> Optional[JWTData]:
    if authorization is None and cookie_token is None:
        raise InvalidToken()

    if authorization:
        _, token = get_authorization_scheme_param(authorization)
    else:
        token = cookie_token

    try:
        payload = jwt.decode(
            cast(str, token), config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
    except JWTError:
        raise InvalidToken()
    else:
        return JWTData(**payload)
