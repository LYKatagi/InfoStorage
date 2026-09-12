from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, VerificationError


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

    def hash_password(self, password):
        return self.hash(password)

    def verify_password(self, hashed_password, password):
        try:
            return self.verify(hashed_password, password)
        except (VerifyMismatchError, VerificationError):
            return False
