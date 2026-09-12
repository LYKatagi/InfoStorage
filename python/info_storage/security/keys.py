import base64
import os

from argon2 import Type
from argon2.low_level import hash_secret_raw

from info_storage.security.fernet import Crypto


class SecurityManager:
    def __init__(
        self,
        time_cost=3,
        memory_cost=66576,
        parallelism=4,
        hash_len=32,
        salt_len=16
    ):
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism
        self.hash_len = hash_len
        self.salt_len = salt_len

        self.salt = None
        self.key = None
        self.crypto = None

    def generate_salt(self):
        return os.urandom(self.salt_len)

    def derive_key(self, password, salt):
        if isinstance(password, str):
            password = password.encode("utf-8")

        raw_key = hash_secret_raw(
            secret=password,
            salt=salt,
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            hash_len=self.hash_len,
            type=Type.ID
        )

        return base64.urlsafe_b64encode(raw_key)

    def setup(self, password):
        self.salt = self.generate_salt()
        self.key = self.derive_key(password, self.salt)
        self.crypto = Crypto(self.key)

        return self.salt

    def unlock(self, password, salt):
        self.salt = salt
        self.key = self.derive_key(password, self.salt)
        self.crypto = Crypto(self.key)

    def encrypt(self, data):
        self._check_unlocked()
        return self.crypto.encrypt_data(data)

    def decrypt(self, data):
        self._check_unlocked()
        return self.crypto.decrypt_data(data)

    def _check_unlocked(self):
        if self.crypto is None:
            raise RuntimeError("O sistema de segurança está bloqueado.")
