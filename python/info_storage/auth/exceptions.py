class AuthException(Exception):
    """Base class for authentication exceptions."""

    pass


class AlreadyAuthenticatedError(AuthException):
    """Raised when an already authenticated user attempts to authenticate again."""

    pass


class InvalidCredentialsError(AuthException):
    """Raised when the provided credentials are invalid."""

    pass


class UserNotAuthenticatedError(AuthException):
    """Raised when an operation requires authentication but the user is not authenticated."""

    pass


class AlreadyExistsError(AuthException):
    """Raised when an attempt is made to create credentials that already exist."""

    pass
