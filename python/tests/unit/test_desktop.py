import json

import pytest

from info_storage.desktop.api_client import RemoteVaultStore
from info_storage.desktop.storage import LocalVaultStore, decode_vault


def test_local_desktop_store_crud_and_reopen(tmp_path):
    store = LocalVaultStore(tmp_path)
    store.create_account("senha-local")
    credential = store.save_item(
        "credentials",
        {
            "title": "Email",
            "username": "ana@example.com",
            "password": "segredo",
            "notes": "",
        },
    )
    note = store.save_item("notes", {"title": "Dica", "content": "privado"})
    store.logout()

    reopened = LocalVaultStore(tmp_path)
    data = reopened.login("senha-local")

    assert data["credentials"][0]["id"] == credential["id"]
    assert data["notes"][0]["id"] == note["id"]
    reopened.delete_item("credentials", credential["id"])
    assert reopened.list_items("credentials") == []


def test_remote_store_requires_https_for_nonlocal_hosts():
    with pytest.raises(Exception, match="HTTPS"):
        RemoteVaultStore("http://vault.example.com")


def test_localhost_http_is_allowed_for_development():
    store = RemoteVaultStore("http://127.0.0.1:8000")
    assert store.api_url == "http://127.0.0.1:8000"


def test_legacy_vault_items_get_stable_ids():
    contents = decode_vault(json.dumps([{"title": "Email", "password": "segredo"}]))

    credential = contents["credentials"][0]
    assert credential["id"]
    assert credential["username"] == ""
    assert contents["notes"] == []


def test_local_registration_rolls_back_when_vault_creation_fails(tmp_path, monkeypatch):
    from info_storage.desktop import storage as desktop_storage

    store = LocalVaultStore(tmp_path)

    def fail_create(self, password, data):
        raise OSError("falha simulada ao criar vault")

    monkeypatch.setattr(desktop_storage.Vault, "create", fail_create)
    with pytest.raises(OSError, match="falha simulada"):
        store.create_account("senha-local")

    assert store.account_exists is False
    assert store.vault.file_path.exists() is False

    monkeypatch.undo()
    store.create_account("senha-local")
    assert store.vault.file_path.exists() is True


def test_remote_store_sends_bearer_and_exposes_collection_crud(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, data, status=200):
            self.data = data
            self.status_code = status
            self.ok = 200 <= status < 300

        def json(self):
            return self.data

    def fake_request(method, url, *, headers, json, timeout):
        calls.append((method, url, headers, json))
        if url.endswith("/auth/login"):
            return FakeResponse({"access_token": "opaque-token"})
        if url.endswith("/credentials") and method == "GET":
            return FakeResponse([])
        if url.endswith("/notes") and method == "GET":
            return FakeResponse([])
        if url.endswith("/credentials") and method == "POST":
            return FakeResponse({"id": "credential-1", **json}, status=201)
        return FakeResponse({}, status=204)

    monkeypatch.setattr(
        "info_storage.desktop.api_client.requests.request", fake_request
    )
    store = RemoteVaultStore("https://vault.example.com")
    assert store.login("ana", "senha") == {"credentials": [], "notes": []}
    assert store.load() == {"credentials": [], "notes": []}

    created = store.save_item(
        "credentials",
        {"title": "Email", "username": "ana", "password": "segredo", "notes": ""},
    )
    store.delete_item("credentials", created["id"])

    assert created["id"] == "credential-1"
    assert all(call[2]["Authorization"] == "Bearer opaque-token" for call in calls[1:])
    assert calls[-1][0] == "DELETE"
