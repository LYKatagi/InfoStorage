import binascii
from pathlib import Path

from info_storage.security.keys import SecurityManager
from info_storage.vault.exceptions import (
    IntegrityError,
    InvalidVaultError,
    VaultAlreadyExistsError,
    VaultLockedError,
)
from info_storage.vault.format import (
    FORMAT_VERSION,
    VAULT_MAGIC,
)
from info_storage.vault.timer import VaultTimer
from info_storage.vault.vault_backend import VaultBackend


class Vault:
    def __init__(self, file_path, timeout=300):
        self.file_path = Path(file_path)

        self.timeout = timeout

        self.security = SecurityManager()
        self.timer = VaultTimer(timeout)

        self.unlocked = False

    def create(self, password, data):
        if self.file_path.exists():
            raise VaultAlreadyExistsError("O cofre já existe.")

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        salt = self.security.setup(password)

        encrypted_data = self.security.encrypt(data)

        backend = VaultBackend(self.security.key)

        content = backend.build(salt, encrypted_data)

        self.file_path.write_bytes(content)

        self.unlocked = True
        self.timer.start()

        return data

    def unlock(self, password):
        if not self.file_path.exists():
            raise InvalidVaultError("O arquivo do cofre não existe.")

        content = self.file_path.read_bytes()

        parts = content.split(b"\n", maxsplit=4)

        if len(parts) != 5:
            raise InvalidVaultError("Estrutura do cofre inválida.")

        magic = parts[0]
        version = parts[1]
        salt_hex = parts[2]

        if magic != VAULT_MAGIC:
            raise InvalidVaultError("Assinatura do cofre inválida.")

        if version != str(FORMAT_VERSION).encode("ascii"):
            raise InvalidVaultError("Versão do cofre não suportada.")

        try:
            salt = binascii.unhexlify(salt_hex)
        except (binascii.Error, ValueError) as error:
            raise InvalidVaultError("Salt inválido.") from error

        if len(salt) != 16:
            raise InvalidVaultError("Salt inválido.")

        self.security.unlock(password, salt)

        backend = VaultBackend(self.security.key)

        try:
            payload = backend.parse(content)
        except IntegrityError:
            self.security = SecurityManager()
            self.unlocked = False
            self.timer.stop()
            raise

        try:
            data = self.security.decrypt(payload.encrypted_data)
        except ValueError as error:
            self.security = SecurityManager()
            self.unlocked = False
            self.timer.stop()

            raise InvalidVaultError(
                "Não foi possível descriptografar o cofre."
            ) from error

        self.unlocked = True
        self.timer.start()

        return data

    def save(self, data):
        self._check_access()

        encrypted_data = self.security.encrypt(data)

        backend = VaultBackend(self.security.key)

        content = backend.build(self.security.salt, encrypted_data)

        self.file_path.write_bytes(content)

        self.timer.reset()

        return data

    def load(self):
        self._check_access()

        content = self.file_path.read_bytes()

        backend = VaultBackend(self.security.key)

        payload = backend.parse(content)

        try:
            data = self.security.decrypt(payload.encrypted_data)
        except ValueError as error:
            raise InvalidVaultError(
                "Não foi possível descriptografar o cofre."
            ) from error

        self.timer.reset()

        return data

    def lock(self):
        self.security = SecurityManager()

        self.unlocked = False

        self.timer.stop()

    def check_timeout(self):
        if not self.unlocked:
            return

        if self.timer.expired():
            self.lock()

            raise VaultLockedError("O cofre foi bloqueado por inatividade.")

    def _check_access(self):
        if not self.unlocked:
            raise VaultLockedError("O cofre está bloqueado.")

        self.check_timeout()

        if not self.unlocked:
            raise VaultLockedError("O cofre está bloqueado.")
