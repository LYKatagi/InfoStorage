from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)


class Hasher(PasswordHasher):
    def __init__(self):
        super().__init__(
            time_cost=3,
            memory_cost=66576,
            parallelism=4,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )

    def hash_password(self, password: str) -> str:
        self._validate_password(password)
        return self.hash(password)

    def verify_password(
        self,
        hashed_password: str,
        password: str,
    ) -> bool:
        self._validate_password(password)

        try:
            return self.verify(hashed_password, password)
        except (
            VerifyMismatchError,
            VerificationError,
            InvalidHashError,
        ):
            return False

    @staticmethod
    def _validate_password(password: str) -> None:
        if not isinstance(password, str):
            raise TypeError("A senha deve ser uma string.")

        if not password:
            raise ValueError("A senha não pode estar vazia.")