from info_storage.auth.exceptions import (
    AlreadyAuthenticatedError,
    InvalidCredentialsError,
    UserNotAuthenticatedError,
)


class Authenticator:
    def __init__(self):
        self._authenticated = False

    @property
    def authenticated(self):
        return self._authenticated

    def authenticate(self, success):
        if self._authenticated:
            raise AlreadyAuthenticatedError("O usuário já está autenticado.")

        if not isinstance(success, bool):
            raise TypeError("O resultado da autenticação deve ser bool.")

        if not success:
            raise InvalidCredentialsError("Credenciais inválidas.")

        self._authenticated = True

    def logout(self):
        self._authenticated = False

    def require_authentication(self):
        if not self._authenticated:
            raise UserNotAuthenticatedError("O usuário não está autenticado.")
