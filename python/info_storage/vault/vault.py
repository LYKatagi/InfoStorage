from pathlib import Path

from info_storage.security.keys import SecurityManager
from info_storage.storage.storage import Storage
from info_storage.vault.exceptions import (
    InvalidVaultError,
    VaultAlreadyExistsError,
    VaultLockedError,
)
from info_storage.vault.format import FORMAT_VERSION, VAULT_MAGIC
from info_storage.vault.timer import VaultTimer


class Vault:
    def __init__(self, file_path, timeout=300.0):
        self.file_path = Path(file_path)

        self.security = SecurityManager()
        self.storage = Storage()
        self.timer = VaultTimer(timeout)

        self.unlocked = False

    def create(self, password, data):
        if self.file_path.exists():
            raise VaultAlreadyExistsError("O cofre já existe.")

        salt = self.security.setup(password)

        encrypted_data = self.security.encrypt(data)

        content = (
            VAULT_MAGIC
            + b"\n"
            + str(FORMAT_VERSION).encode("ascii")
            + b"\n"
            + salt
            + b"\n"
            + encrypted_data
        )

        self.storage.save(self.file_path, content, storage_type="dat")

        self.unlocked = True
        self.timer.start()

    def unlock(self, password):
        content = self.storage.load(self.file_path, storage_type="dat")

        parts = content.split(b"\n", maxsplit=3)

        if len(parts) != 4:
            raise InvalidVaultError("Estrutura do cofre inválida.")

        magic, version, salt, encrypted_data = parts

        if magic != VAULT_MAGIC:
            raise InvalidVaultError("Assinatura do cofre inválida.")

        if version != str(FORMAT_VERSION).encode("ascii"):
            raise InvalidVaultError("Versão do cofre não suportada.")

        self.security.unlock(password, salt)

        try:
            decrypted_data = self.security.decrypt(encrypted_data)
        except ValueError as error:
            raise InvalidVaultError("Senha incorreta ou dados corrompidos.") from error

        self.unlocked = True
        self.timer.start()

        return decrypted_data

    def save(self, data):
        self._check_access()

        encrypted_data = self.security.encrypt(data)

        content = (
            VAULT_MAGIC
            + b"\n"
            + str(FORMAT_VERSION).encode("ascii")
            + b"\n"
            + self.security.salt
            + b"\n"
            + encrypted_data
        )

        self.storage.save(self.file_path, content, storage_type="dat")

        self.timer.reset()

    def load(self):
        self._check_access()

        content = self.storage.load(self.file_path, storage_type="dat")

        parts = content.split(b"\n", maxsplit=3)

        if len(parts) != 4:
            raise InvalidVaultError("Estrutura do cofre inválida.")

        _, _, _, encrypted_data = parts

        data = self.security.decrypt(encrypted_data)

        self.timer.reset()

        return data

    def lock(self):
        self.security = SecurityManager()
        self.unlocked = False
        self.timer.stop()

    def check_timeout(self):
        if self.unlocked and self.timer.expired():
            self.lock()

    def _check_access(self):
        self.check_timeout()

        if not self.unlocked:
            raise VaultLockedError("O cofre está bloqueado.")
