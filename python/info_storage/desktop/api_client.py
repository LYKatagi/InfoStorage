from typing import Any
from urllib.parse import urlparse

import requests

from info_storage.desktop.storage import Collection


class DesktopAPIError(Exception):
    pass


class RemoteVaultStore:
    def __init__(self, api_url: str, timeout: float = 12.0):
        self.api_url = api_url.strip().rstrip("/")
        self.timeout = timeout
        self.token: str | None = None
        self._validate_url()

    def register(self, username: str, password: str) -> dict[str, list[dict]]:
        return self._authenticate("/api/v1/auth/register", username, password)

    def login(self, username: str, password: str) -> dict[str, list[dict]]:
        return self._authenticate("/api/v1/auth/login", username, password)

    def list_items(self, collection: Collection) -> list[dict]:
        response = self._request("GET", f"/api/v1/{collection}")
        return response

    def load(self) -> dict[str, list[dict]]:
        return {
            "credentials": self.list_items("credentials"),
            "notes": self.list_items("notes"),
        }

    def save_item(
        self,
        collection: Collection,
        values: dict[str, str],
        item_id: str | None = None,
    ) -> dict:
        path = f"/api/v1/{collection}"
        if item_id:
            path = f"{path}/{item_id}"
        return self._request("PUT" if item_id else "POST", path, body=values)

    def delete_item(self, collection: Collection, item_id: str) -> None:
        self._request("DELETE", f"/api/v1/{collection}/{item_id}")

    def logout(self) -> None:
        if self.token is None:
            return
        try:
            self._request("POST", "/api/v1/auth/logout")
        finally:
            self.token = None

    def _authenticate(
        self, route: str, username: str, password: str
    ) -> dict[str, list[dict]]:
        response = self._request(
            "POST",
            route,
            authenticated=False,
            body={"username": username, "password": password},
        )
        self.token = response["access_token"]
        try:
            return {
                "credentials": self.list_items("credentials"),
                "notes": self.list_items("notes"),
            }
        except Exception:
            self.token = None
            raise

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if authenticated and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = requests.request(
                method,
                f"{self.api_url}{path}",
                headers=headers,
                json=body,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise DesktopAPIError("Não foi possível conectar à API.") from error
        if response.status_code == 204:
            return None
        try:
            data = response.json()
        except ValueError:
            data = {}
        if not response.ok:
            if response.status_code == 401:
                self.token = None
            raise DesktopAPIError(str(data.get("detail", "Falha na API.")))
        return data

    def _validate_url(self) -> None:
        parsed = urlparse(self.api_url)
        if not parsed.hostname:
            raise DesktopAPIError("Informe uma URL válida para a API.")
        local_hosts = {"localhost", "127.0.0.1", "10.0.2.2"}
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in local_hosts
        ):
            raise DesktopAPIError("Use HTTPS para sincronizar com servidores remotos.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise DesktopAPIError("A URL não pode conter credenciais ou query string.")
