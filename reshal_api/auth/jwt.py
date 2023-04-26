from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends
from jose import JWTError, jwt

from reshal_api.config import get_config

from .exceptions import InvalidToken
from .models import User
from .schemas import JWTData
from .security import OAuth2PasswordBearerCookie

config = get_config()

oauth2_scheme = OAuth2PasswordBearerCookie(token_url="/auth/token")


def create_access_token(user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE)
    return jwt.encode(
        {"exp": expire, "user_id": str(user.id), "is_superuser": user.is_superuser},
        key=config.SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def get_data_from_token(token: str = Depends(oauth2_scheme)) -> Optional[JWTData]:
    if not token:
        raise InvalidToken()
    try:
        payload = jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
    except JWTError:
        raise InvalidToken()
    else:
        return JWTData(**payload)
