from typing import Any

import requests


class APIError(Exception):
    def __init__(self, status_code: int | None, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class InfoStorageAPI:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def register(self, username: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/auth/register",
            json={"username": username, "password": password},
        )

    def login(self, username: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    def logout(self, token: str) -> None:
        self._request("POST", "/api/v1/auth/logout", token=token)

    def summary(self, token: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/vault/summary", token=token)

    def search(self, token: str, query: str) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/search", token=token, params={"q": query})

    def list_credentials(self, token: str) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/credentials", token=token)

    def create_credential(self, token: str, values: dict[str, str]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/credentials", token=token, json=values)

    def delete_credential(self, token: str, credential_id: str) -> None:
        self._request("DELETE", f"/api/v1/credentials/{credential_id}", token=token)

    def list_notes(self, token: str) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/notes", token=token)

    def create_note(self, token: str, values: dict[str, str]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/notes", token=token, json=values)

    def delete_note(self, token: str, note_id: str) -> None:
        self._request("DELETE", f"/api/v1/notes/{note_id}", token=token)

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        headers = {"Accept": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                json=json,
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise APIError(None, "A API InfoStorage está indisponível.") from error

        if response.status_code == 204:
            return None
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not response.ok:
            detail = payload.get("detail", "Não foi possível concluir a operação.")
            raise APIError(response.status_code, str(detail))
        return payload
