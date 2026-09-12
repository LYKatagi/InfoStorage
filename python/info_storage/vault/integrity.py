import hashlib
import hmac


class IntegrityChecker:
    @staticmethod
    def generate(data, key):
        if isinstance(data, str):
            data = data.encode("utf-8")

        return hmac.new(
            key,
            data,
            hashlib.sha256
        ).digest()

    @staticmethod
    def verify(data, signature, key):
        expected_signature = IntegrityChecker.generate(
            data,
            key
        )

        return hmac.compare_digest(
            expected_signature,
            signature
        )
