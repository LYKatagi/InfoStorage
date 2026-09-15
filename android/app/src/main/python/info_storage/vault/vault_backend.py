import binascii
from dataclasses import dataclass

from info_storage.vault.exceptions import IntegrityError, InvalidVaultError
from info_storage.vault.format import FORMAT_VERSION, VAULT_MAGIC
from info_storage.vault.integrity import IntegrityChecker


@dataclass
class VaultPayload:
    salt: bytes
    encrypted_data: bytes


class VaultBackend:
    def __init__(self, key):
        self.key = key

    def build(self, salt, encrypted_data):
        signature = IntegrityChecker.generate(encrypted_data, self.key)

        salt_hex = binascii.hexlify(salt)
        signature_hex = binascii.hexlify(signature)

        return (
            VAULT_MAGIC
            + b"\n"
            + str(FORMAT_VERSION).encode("ascii")
            + b"\n"
            + salt_hex
            + b"\n"
            + signature_hex
            + b"\n"
            + encrypted_data
        )

    def parse(self, content):
        parts = content.split(b"\n", maxsplit=4)

        if len(parts) != 5:
            raise InvalidVaultError("Estrutura do cofre inválida.")

        (magic, version, salt_hex, signature_hex, encrypted_data) = parts

        if magic != VAULT_MAGIC:
            raise InvalidVaultError("Assinatura do cofre inválida.")

        if version != str(FORMAT_VERSION).encode("ascii"):
            raise InvalidVaultError("Versão do cofre não suportada.")

        try:
            salt = binascii.unhexlify(salt_hex)
            signature = binascii.unhexlify(signature_hex)

        except (binascii.Error, ValueError) as error:
            raise InvalidVaultError(
                "Dados codificados do cofre são inválidos."
            ) from error

        if len(salt) != 16:
            raise InvalidVaultError("Salt inválido.")

        if len(signature) != 32:
            raise InvalidVaultError("Assinatura de integridade inválida.")

        if not IntegrityChecker.verify(encrypted_data, signature, self.key):
            raise IntegrityError("A integridade do cofre foi comprometida.")

        return VaultPayload(salt=salt, encrypted_data=encrypted_data)
