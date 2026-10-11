import hashlib
import json
import shutil
import uuid
from pathlib import Path
from threading import RLock
from typing import Literal

from info_storage.auth.authenticator import Authenticator
from info_storage.auth.exceptions import InvalidCredentialsError
from info_storage.vault.exceptions import VaultError
from info_storage.vault.vault import Vault
from info_storage.web.sessions import AccountSession

Collection = Literal["credentials", "notes"]


class AccountAlreadyExistsError(Exception):
    pass


class InvalidLoginError(Exception):
    pass


class InvalidVaultDataError(ValueError):
    pass


class AccountStore:
    def __init__(self, data_dir: Path, session_ttl_seconds: int):
        self.users_dir = data_dir / "users"
        self.session_ttl_seconds = session_ttl_seconds
        self._registration_lock = RLock()
        self._account_locks: dict[str, RLock] = {}
        self._account_locks_lock = RLock()

    def register(self, username: str, password: str) -> AccountSession:
        account_key = self._account_key(username)
        user_dir = self.users_dir / account_key
        lock = self._lock_for(account_key)

        with lock, self._registration_lock:
            self.users_dir.mkdir(parents=True, exist_ok=True)
            try:
                user_dir.mkdir()
            except FileExistsError as error:
                raise AccountAlreadyExistsError from error

            authenticator = Authenticator(user_dir / "credentials.json")
            vault = Vault(
                user_dir / "vault.dat",
                timeout=self.session_ttl_seconds,
                security=authenticator.security,
            )
            try:
                authenticator.register(password)
                authenticator.authenticate(password)
                initial_data = json.dumps(
                    {"credentials": [], "notes": []}, ensure_ascii=False
                )
                vault.create(password, initial_data)
            except Exception:
                vault.lock()
                if authenticator.authenticated:
                    authenticator.logout()
                shutil.rmtree(user_dir, ignore_errors=True)
                raise

        return AccountSession(username, account_key, authenticator, vault, lock)

    def login(self, username: str, password: str) -> AccountSession:
        account_key = self._account_key(username)
        user_dir = self.users_dir / account_key
        lock = self._lock_for(account_key)

        with lock:
            authenticator = Authenticator(user_dir / "credentials.json")
            vault = Vault(
                user_dir / "vault.dat",
                timeout=self.session_ttl_seconds,
                security=authenticator.security,
            )
            try:
                authenticator.authenticate(password)
            except (InvalidCredentialsError, FileNotFoundError, ValueError, TypeError):
                raise InvalidLoginError from None

            try:
                vault.unlock(password)
                contents = self._decode_contents(vault.load())
                vault.save(json.dumps(contents, ensure_ascii=False))
            except (VaultError, OSError, ValueError, TypeError) as error:
                vault.lock()
                authenticator.logout()
                raise InvalidVaultDataError from error

        return AccountSession(username, account_key, authenticator, vault, lock)

    def list_items(self, session: AccountSession, collection: Collection) -> list[dict]:
        return self._load_contents(session)[collection]

    def get_item(
        self, session: AccountSession, collection: Collection, item_id: str
    ) -> dict | None:
        return next(
            (
                item
                for item in self._load_contents(session)[collection]
                if item["id"] == item_id
            ),
            None,
        )

    def create_item(
        self, session: AccountSession, collection: Collection, values: dict
    ) -> dict:
        contents = self._load_contents(session)
        item = {"id": str(uuid.uuid4()), **values}
        contents[collection].append(item)
        self._save_contents(session, contents)
        return item

    def update_item(
        self,
        session: AccountSession,
        collection: Collection,
        item_id: str,
        values: dict,
    ) -> dict | None:
        contents = self._load_contents(session)
        for index, item in enumerate(contents[collection]):
            if item["id"] == item_id:
                updated = {"id": item_id, **values}
                contents[collection][index] = updated
                self._save_contents(session, contents)
                return updated
        return None

    def delete_item(
        self, session: AccountSession, collection: Collection, item_id: str
    ) -> bool:
        contents = self._load_contents(session)
        remaining = [item for item in contents[collection] if item["id"] != item_id]
        if len(remaining) == len(contents[collection]):
            return False
        contents[collection] = remaining
        self._save_contents(session, contents)
        return True

    def _load_contents(self, session: AccountSession) -> dict[str, list[dict]]:
        try:
            return self._decode_contents(session.vault.load())
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            raise InvalidVaultDataError from error

    @staticmethod
    def _decode_contents(data: str) -> dict[str, list[dict]]:
        decoded = json.loads(data) if data else {"credentials": [], "notes": []}
        if isinstance(decoded, list):
            decoded = {"credentials": decoded, "notes": []}
        if not isinstance(decoded, dict):
            raise InvalidVaultDataError

        result = {}
        for collection in ("credentials", "notes"):
            items = decoded.get(collection, [])
            if not isinstance(items, list) or any(
                not isinstance(item, dict) for item in items
            ):
                raise InvalidVaultDataError
            result[collection] = [
                AccountStore._normalize_item(item, collection) for item in items
            ]
        return result

    @staticmethod
    def _normalize_item(item: dict, collection: str) -> dict:
        normalized = dict(item)
        if not normalized.get("id"):
            canonical = json.dumps(item, sort_keys=True, ensure_ascii=False)
            normalized["id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[
                :32
            ]
        normalized.setdefault("title", "Sem título")
        if collection == "credentials":
            normalized.setdefault("username", "")
            normalized.setdefault("password", "")
            normalized.setdefault("notes", "")
        else:
            normalized.setdefault("content", "")
        return normalized

    @staticmethod
    def _save_contents(
        session: AccountSession, contents: dict[str, list[dict]]
    ) -> None:
        session.vault.save(json.dumps(contents, ensure_ascii=False))

    @staticmethod
    def _account_key(username: str) -> str:
        normalized = username.strip().casefold()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _lock_for(self, account_key: str) -> RLock:
        with self._account_locks_lock:
            return self._account_locks.setdefault(account_key, RLock())
