from reshal_api.exceptions import Conflict, Forbidden, NotAuthenticated, NotFound


class InvalidAuthRequest(NotAuthenticated):
    ...


class InvalidToken(NotAuthenticated):
    ...


class UserNotFound(NotFound):
    ...


class UserIsNotSuperuser(Forbidden):
    ...


class UserRoleNotSufficient(Forbidden):
    ...


class EmailAlreadyExists(Conflict):
    def __init__(self):
        super().__init__(detail="Email already exists")
