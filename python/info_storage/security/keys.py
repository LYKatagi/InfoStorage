import base64
import os

from argon2 import Type
from argon2.low_level import hash_secret_raw

from info_storage.security.argon2 import Hasher
from info_storage.security.fernet import Crypto


class SecurityManager:
    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 66576,
        parallelism: int = 4,
        hash_len: int = 32,
        salt_len: int = 16,
    ):
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism
        self.hash_len = hash_len
        self.salt_len = salt_len

        self.hasher = Hasher()

        self.salt: bytes | None = None
        self.key: bytes | None = None
        self.crypto: Crypto | None = None

    @property
    def unlocked(self) -> bool:
        return self.crypto is not None

    def generate_salt(self) -> bytes:
        return os.urandom(self.salt_len)

    def derive_key(
        self,
        password: str,
        salt: bytes,
    ) -> bytes:
        if not isinstance(password, str):
            raise TypeError("A senha deve ser uma string.")

        if not isinstance(salt, bytes):
            raise TypeError("O salt deve ser bytes.")

        raw_key = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            hash_len=self.hash_len,
            type=Type.ID,
        )

        return base64.urlsafe_b64encode(raw_key)

    def setup(self, password: str) -> bytes:
        salt = self.generate_salt()
        self.unlock(password, salt)
        return salt

    def unlock(
        self,
        password: str,
        salt: bytes,
    ) -> None:
        self.salt = salt
        self.key = self.derive_key(password, salt)
        self.crypto = Crypto(self.key)

    def lock(self) -> None:
        self.salt = None
        self.key = None
        self.crypto = None

    def encrypt(self, data: str | bytes) -> str:
        self._check_unlocked()
        return self.crypto.encrypt_data(data)

    def decrypt(self, data: str | bytes) -> str:
        self._check_unlocked()
        return self.crypto.decrypt_data(data)

    def verify_password(
        self,
        hashed_password: str,
        password: str,
    ) -> bool:
        return self.hasher.verify_password(
            hashed_password,
            password,
        )

    def _check_unlocked(self) -> None:
        if self.crypto is None:
            raise RuntimeError(
                "O sistema de segurança está bloqueado."
            )