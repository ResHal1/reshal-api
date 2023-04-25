from fastapi import HTTPException, status


class BaseHttpException(HTTPException):
    def __init__(self, status_code: int, detail: str, *args, **kwargs):
        super().__init__(status_code=status_code, detail=detail, *args, **kwargs)


class Forbidden(BaseHttpException):
    """HTTP_403_FORBIDDEN"""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotAuthenticated(BaseHttpException):
    """HTTP_401_UNAUTHORIZED"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


class NotFound(BaseHttpException):
    """HTTP_404_NOT_FOUND"""

    def __init__(self, detail: str = "Not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequest(BaseHttpException):
    """HTTP_400_BAD_REQUEST"""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class Conflict(BaseHttpException):
    """HTTP_409_CONFLICT"""

    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
