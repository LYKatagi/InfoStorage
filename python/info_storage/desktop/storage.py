import hashlib
import json
import uuid
from pathlib import Path
from typing import Literal

from info_storage.auth.authenticator import Authenticator
from info_storage.vault.vault import Vault

Collection = Literal["credentials", "notes"]
EMPTY_VAULT = {"credentials": [], "notes": []}


class LocalVaultStore:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.authenticator = Authenticator(data_dir / "credentials.json")
        self.vault = Vault(
            data_dir / "vault.dat",
            security=self.authenticator.security,
        )

    @property
    def account_exists(self) -> bool:
        return self.authenticator.credentials.exists()

    def create_account(self, password: str) -> dict[str, list[dict]]:
        self.authenticator.register(password)
        try:
            self.authenticator.authenticate(password)
            self.vault.create(password, json.dumps(EMPTY_VAULT, ensure_ascii=False))
        except Exception:
            self.vault.lock()
            if self.authenticator.authenticated:
                self.authenticator.logout()
            raise
        return EMPTY_VAULT.copy()

    def login(self, password: str) -> dict[str, list[dict]]:
        self.authenticator.authenticate(password)
        try:
            contents = decode_vault(self.vault.unlock(password))
            self.vault.save(json.dumps(contents, ensure_ascii=False))
            return contents
        except Exception:
            self.vault.lock()
            self.authenticator.logout()
            raise

    def list_items(self, collection: Collection) -> list[dict]:
        return decode_vault(self.vault.load())[collection]

    def load(self) -> dict[str, list[dict]]:
        return decode_vault(self.vault.load())

    def save_item(
        self,
        collection: Collection,
        values: dict[str, str],
        item_id: str | None = None,
    ) -> dict:
        contents = decode_vault(self.vault.load())
        item = {"id": item_id or str(uuid.uuid4()), **values}
        if item_id is None:
            contents[collection].append(item)
        else:
            for index, existing in enumerate(contents[collection]):
                if existing["id"] == item_id:
                    contents[collection][index] = item
                    break
            else:
                raise KeyError("Item não encontrado.")
        self._save(contents)
        return item

    def delete_item(self, collection: Collection, item_id: str) -> None:
        contents = decode_vault(self.vault.load())
        remaining = [item for item in contents[collection] if item["id"] != item_id]
        if len(remaining) == len(contents[collection]):
            raise KeyError("Item não encontrado.")
        contents[collection] = remaining
        self._save(contents)

    def logout(self) -> None:
        self.vault.lock()
        if self.authenticator.authenticated:
            self.authenticator.logout()

    def _save(self, contents: dict[str, list[dict]]) -> None:
        self.vault.save(json.dumps(contents, ensure_ascii=False))


def decode_vault(data: str) -> dict[str, list[dict]]:
    decoded = json.loads(data) if data else EMPTY_VAULT.copy()
    if isinstance(decoded, list):
        decoded = {"credentials": decoded, "notes": []}
    if not isinstance(decoded, dict):
        raise ValueError("O conteúdo do cofre está inválido.")

    result: dict[str, list[dict]] = {}
    for collection in ("credentials", "notes"):
        items = decoded.get(collection, [])
        if not isinstance(items, list) or any(
            not isinstance(item, dict) for item in items
        ):
            raise ValueError("O conteúdo do cofre está inválido.")
        normalized = []
        for source in items:
            item = dict(source)
            if not item.get("id"):
                stable = json.dumps(item, sort_keys=True, ensure_ascii=False)
                item["id"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:32]
            item.setdefault("title", "Sem título")
            if collection == "credentials":
                item.setdefault("username", "")
                item.setdefault("password", "")
                item.setdefault("notes", "")
            else:
                item.setdefault("content", "")
            normalized.append(item)
        result[collection] = normalized
    return result
