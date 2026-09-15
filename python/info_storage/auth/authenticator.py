from pathlib import Path

from info_storage.auth.credentials import Credentials
from info_storage.auth.exceptions import (
    AlreadyAuthenticatedError,
    InvalidCredentialsError,
    UserNotAuthenticatedError,
    AlreadyExistsError,
)
from info_storage.security.keys import SecurityManager


class Authenticator:
    def __init__(
        self,
        credentials_path: str | Path,
        security: SecurityManager | None = None,
    ):
        self.security = security or SecurityManager()

        self.credentials = Credentials(
            file_path=credentials_path,
            security=self.security,
        )

        self._authenticated = False
    def authenticate_with_vault(
        self,
        password: str,
        salt: bytes,
    ) -> None:
        self.authenticate(password)
        self.security.unlock(password, salt)
    @property
    def authenticated(self) -> bool:
        return self._authenticated

    def register(self, password: str) -> None:
        if self.credentials.exists():
            raise AlreadyExistsError(
                "As credenciais já estão cadastradas."
            )

        self.credentials.create(password)

    def authenticate(self, password: str) -> None:
        if self._authenticated:
            raise AlreadyAuthenticatedError(
                "O usuário já está autenticado."
            )

        try:
            valid = self.credentials.verify(password)
        except FileNotFoundError as error:
            raise InvalidCredentialsError(
                "As credenciais não foram encontradas."
            ) from error

        if not valid:
            raise InvalidCredentialsError(
                "Senha incorreta."
            )

        self._authenticated = True

    def logout(self) -> None:
        if not self._authenticated:
            raise UserNotAuthenticatedError(
                "O usuário não está autenticado."
            )

        self._authenticated = False
        self.security.lock()

    def require_authentication(self) -> None:
        if not self._authenticated:
            raise UserNotAuthenticatedError(
                "Autenticação necessária."
            )