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
        return json.dumps(
            {"success": success, "message": message, **extra}, ensure_ascii=False
        )
        # ... adicione este método dentro da classe InfoStorageApp no mobile_api.py

    def generate_secure_password(self, length: int = 16, use_uppercase: bool = True, 
                                 use_numbers: bool = True, use_symbols: bool = True) -> str:
        """Gera uma senha aleatória de alta entropia usando o módulo secrets do Python."""
        import secrets
        import string

        # Base obrigatória: letras minúsculas
        chars = string.ascii_lowercase
        
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_numbers:
            chars += string.digits
        if use_symbols:
            # Símbolos seguros comuns para formulários web
            chars += "!@#$%^&*()-_=+[]{}|;:,."

        try:
            # Garante que pelo menos um caractere de cada grupo selecionado esteja na senha
            # para evitar senhas geradas aleatoriamente que falham em validações de sites
            password = []
            if use_uppercase: password.append(secrets.choice(string.ascii_uppercase))
            if use_numbers: password.append(secrets.choice(string.digits))
            if use_symbols: password.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,."))
            
            # Preenche o restante do tamanho solicitado
            remaining_length = length - len(password)
            if remaining_length < 0:
                password.extend([secrets.choice(chars) for _ in range(remaining_length)])
            
            # Embaralha a lista para que os caracteres obrigatórios não fiquem sempre no início
            secrets.SystemRandom().shuffle(password)
            
            generated_str = "".join(password)
            return self._result(True, "Senha gerada com sucesso.", password=generated_str)
        except Exception as error:
            return self._result(False, f"Erro ao gerar senha: {str(error)}")

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
                return self._result(
                    True, "Cofre desbloqueado.", data=self._decode_records(data)
                )

            initial_vault = {"credentials": [], "notes": []}
            self.vault.create(password, json.dumps(initial_vault, ensure_ascii=False))
            return self._result(True, "Cofre criado com sucesso.", data=initial_vault)
        except Exception as error:
            self._clear_session()
            return self._result(False, str(error))

    def login_json(self, password: str) -> str:
        try:
            self.authenticator.authenticate(password)
            if not self.vault_path.exists():
                return self._result(
                    True,
                    "Sessão iniciada. Crie seu cofre para continuar.",
                    needs_vault=True,
                )

            data = self.vault.unlock(password)
            return self._result(
                True, "Cofre desbloqueado.", data=self._decode_records(data)
            )
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
            if not isinstance(records, list) and not isinstance(records, dict):
                raise ValueError("Os dados do cofre precisam ser estruturados.")
            self.vault.save(json.dumps(records, ensure_ascii=False))
            return self._result(True, "Alterações salvas.", data=records)
        except Exception as error:
            expired = not self.vault.unlocked
            if expired:
                self._clear_session()
            return self._result(False, str(error), requires_login=expired)

    def add_note_json(self, note_json: str) -> str:
        try:
            new_note = json.loads(note_json)
            current_vault = self._load_records()
            current_vault["notes"].append(new_note)
            self.vault.save(json.dumps(current_vault, ensure_ascii=False))
            return self._result(
                True, "Nota salva com sucesso.", data=current_vault["notes"]
            )
        except Exception as error:
            expired = not self.vault.unlocked
            if expired:
                self._clear_session()
            return self._result(False, str(error), requires_login=expired)

    def get_notes_json(self) -> str:
        try:
            current_vault = self._load_records()
            return self._result(
                True, "Notas carregadas.", data=current_vault.get("notes", [])
            )
        except Exception as error:
            expired = not self.vault.unlocked
            if expired:
                self._clear_session()
            return self._result(False, str(error), requires_login=expired)

    def logout_json(self) -> str:
        try:
            self._clear_session()
            return self._result(True, "Cofre bloqueado.")
        except Exception as error:
            self._clear_session()
            return self._result(False, str(error))

    def _load_records(self):
        return self._decode_records(self.vault.load())

    @staticmethod
    def _decode_records(data):
        if not data:
            return {"credentials": [], "notes": []}

        records = json.loads(data)
        if isinstance(records, list):
            return {"credentials": records, "notes": []}

        if not isinstance(records, dict):
            raise ValueError("O conteúdo do cofre está inválido.")

        if "credentials" not in records:
            records["credentials"] = []
        if "notes" not in records:
            records["notes"] = []

        return records

    def _clear_session(self) -> None:
        """Lock the vault and discard the active authentication state."""
        self.vault.lock()
        if self.authenticator.authenticated:
            self.authenticator.logout()
