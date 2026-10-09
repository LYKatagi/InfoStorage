"""JSON adapter used by the Android application through PythonBridge."""

import json
from pathlib import Path

from info_storage.auth.authenticator import Authenticator
from info_storage.auth.exceptions import AlreadyExistsError, InvalidCredentialsError
from info_storage.vault.vault import Vault


class InfoStorageApp:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.authenticator = Authenticator(self.base_dir / "credentials.json")
        self.vault_path = self.base_dir / "vault.dat"
        self.vault = Vault(self.vault_path, security=self.authenticator.security)

    def _result(self, success: bool, message: str, **extra) -> str:
        return json.dumps({"success": success, "message": message, **extra}, ensure_ascii=False)

    def get_status_json(self) -> str:
        return self._result(
            True,
            "Status atualizado.",
            account_exists=self.authenticator.credentials.exists(),
            vault_exists=self.vault_path.exists(),
            authenticated=self.authenticator.authenticated,
            unlocked=self.vault.unlocked,
        )

    def register_json(self, password: str) -> str:
        try:
            self.authenticator.register(password)
            self.authenticator.authenticate(password)
            return self._result(True, "Conta criada com sucesso.", authenticated=True)
        except (AlreadyExistsError, ValueError, TypeError) as error:
            return self._result(False, str(error))

    def create_vault_json(self, password: str) -> str:
        try:
            if not self.authenticator.authenticated:
                self.authenticator.authenticate(password)
            if self.vault_path.exists():
                data = self.vault.unlock(password)
                return self._result(True, "Cofre desbloqueado.", data=self._decode_records(data))
            self.vault.create(password, json.dumps([], ensure_ascii=False))
            return self._result(True, "Cofre criado com sucesso.", data=[])
        except Exception as error:
            self._clear_session()
            return self._result(False, str(error))

    def login_json(self, password: str) -> str:
        try:
            self.authenticator.authenticate(password)
            if not self.vault_path.exists():
                return self._result(True, "Sessão iniciada. Crie seu cofre para continuar.", needs_vault=True)
            data = self.vault.unlock(password)
            return self._result(True, "Cofre desbloqueado.", data=self._decode_records(data))
        except (InvalidCredentialsError, ValueError, TypeError) as error:
            self._clear_session()
            return self._result(False, str(error))
        except Exception as error:
            self._clear_session()
            return self._result(False, str(error))

    def load_data_json(self) -> str:
        try:
            return self._result(True, "Dados carregados.", data=self._load_records())
        except Exception as error:
            expired = not self.vault.unlocked
            if expired:
                self._clear_session()
            return self._result(False, str(error), requires_login=expired)

    def save_data_json(self, data_json: str) -> str:
        try:
            records = json.loads(data_json)
            if not isinstance(records, list):
                raise ValueError("Os dados do cofre precisam ser uma lista.")
            self.vault.save(json.dumps(records, ensure_ascii=False))
            return self._result(True, "Alterações salvas.", data=records)
        except Exception as error:
            expired = not self.vault.unlocked
            if expired:
                self._clear_session()
            return self._result(False, str(error), requires_login=expired)

    def logout_json(self) -> str:
        try:
            self.vault.lock()
            if self.authenticator.authenticated:
                self.authenticator.logout()
            return self._result(True, "Cofre bloqueado.")
        except Exception as error:
            self._clear_session()
            return self._result(False, str(error))

    def _load_records(self):
        return self._decode_records(self.vault.load())

    @staticmethod
    def _decode_records(data):
        if not data:
            return []
        records = json.loads(data)
        if not isinstance(records, list):
            raise ValueError("O conteúdo do cofre está inválido.")
        return records

    def _clear_session(self) -> None:
        self.vault.lock()
        if self.authenticator.authenticated:
            self.authenticator.logout()
