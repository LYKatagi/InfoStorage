from pathlib import Path

from info_storage.security.keys import SecurityManager
from info_storage.storage.json import JSONStorage


class Credentials:
    def __init__(
        self,
        file_path: str | Path,
        security: SecurityManager | None = None,
    ):
        self.file_path = Path(file_path)
        self.security = security or SecurityManager()
        self.storage = JSONStorage()

    def exists(self) -> bool:
        return self.file_path.exists()

    def create(self, password: str) -> None:
        if self.exists():
            raise FileExistsError(
                "As credenciais já existem."
            )

        self._validate_password(password)

        password_hash = self.security.hasher.hash_password(
            password
        )

        data = {
            "version": 1,
            "password_hash": password_hash,
        }

        self.storage.save(self.file_path, data)

    def verify(self, password: str) -> bool:
        if not self.exists():
            raise FileNotFoundError(
                "O arquivo de credenciais não existe."
            )

        self._validate_password(password)

        data = self.storage.load(self.file_path)
        password_hash = data.get("password_hash")

        if not isinstance(password_hash, str):
            return False

        return self.security.verify_password(
            password_hash,
            password,
        )

    def load(self) -> dict:
        if not self.exists():
            raise FileNotFoundError(
                "O arquivo de credenciais não existe."
            )

        return self.storage.load(self.file_path)

    @staticmethod
    def _validate_password(password: str) -> None:
        if not isinstance(password, str):
            raise TypeError(
                "A senha deve ser uma string."
            )

        if not password:
            raise ValueError(
                "A senha não pode estar vazia."
            )