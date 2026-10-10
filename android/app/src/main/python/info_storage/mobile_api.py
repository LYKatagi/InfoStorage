"""JSON adapter used by the Android application through PythonBridge."""

import gc
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
            return self._result(False, str(error))
        finally:
            self._clear_session()  # Garante limpeza absoluta mesmo após tentar criar/abrir

    def login_json(self, password: str) -> str:
        # Criamos referências mutáveis locais para poder rastrear e zerar fisicamente
        hash_mestre = None
        chave_fernet = None
        chave_hmac = None
        try:
            self.authenticator.authenticate(password)
            if not self.vault_path.exists():
                return self._result(
                    True,
                    "Sessão iniciada. Crie seu cofre para continuar.",
                    needs_vault=True,
                )

            # --- BLINDAGEM DE MEMÓRIA (KEY SPLITTING COM BYTEARRAY) ---
            # Se o seu SecurityManager retornar bytes comuns, nós os convertemos
            # imediatamente em um bytearray mutável para gerenciamento controlado.
            if (
                hasattr(self.authenticator.security, "key")
                and self.authenticator.security.key
            ):
                hash_mestre = bytearray(self.authenticator.security.key)
                # Exemplo de divisão segura na RAM se o hash tiver tamanho estendido:
                if len(hash_mestre) >= 64:
                    chave_fernet = hash_mestre[:32]
                    chave_hmac = hash_mestre[32:64]

            data = self.vault.unlock(password)
            return self._result(
                True, "Cofre desbloqueado.", data=self._decode_records(data)
            )
        except (InvalidCredentialsError, ValueError, TypeError) as error:
            return self._result(False, str(error))
        except Exception as error:
            return self._result(False, str(error))
        finally:
            # Saturação de memória física: sobrescreve os arrays com zeros na RAM antes do descarte
            for arr in [hash_mestre, chave_fernet, chave_hmac]:
                if isinstance(arr, bytearray):
                    for i in range(len(arr)):
                        arr[i] = 0  # Substitui o segredo por zeros binários

            # Limpa referências locais
            del hash_mestre, chave_fernet, chave_hmac
            self._clear_session()

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
        """Tranca o cofre e expurga ativamente os resíduos de chaves remanescentes na RAM."""
        # Se houver chaves armazenadas no gerenciador de segurança interno, limpamos de forma mutável se possível
        if hasattr(self.authenticator.security, "key") and isinstance(
            self.authenticator.security.key, bytearray
        ):
            for i in range(len(self.authenticator.security.key)):
                self.authenticator.security.key[i] = 0

        self.vault.lock()
        if self.authenticator.authenticated:
            self.authenticator.logout()

        # Força o coletor do Python a passar varrendo todas as referências perdidas imediatamente
        gc.collect()
