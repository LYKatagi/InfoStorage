from fastapi.testclient import TestClient

from info_storage.web.config import Settings
from info_storage.web.main import create_app


def create_client(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, session_ttl_seconds=600))
    return TestClient(app)


def register(client, username="ana", password="senha-forte"):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_private_collections_require_a_session(tmp_path):
    client = create_client(tmp_path)

    assert client.get("/api/v1/credentials").status_code == 401
    assert client.get("/api/v1/notes").status_code == 401
    assert client.get("/api/v1/vault/summary").status_code == 401
    assert client.get("/api/v1/search?q=segredo").status_code == 401


def test_credentials_crud_and_session_logout(tmp_path):
    client = create_client(tmp_path)
    headers = register(client)
    payload = {
        "title": "Email",
        "username": "ana@example.com",
        "password": "segredo",
        "notes": "Conta pessoal",
    }

    created = client.post("/api/v1/credentials", json=payload, headers=headers)
    assert created.status_code == 201
    credential_id = created.json()["id"]
    assert (
        client.get("/api/v1/credentials", headers=headers).json()[0]["password"]
        == "segredo"
    )

    changed = {**payload, "password": "novo-segredo"}
    updated = client.put(
        f"/api/v1/credentials/{credential_id}", json=changed, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["password"] == "novo-segredo"
    assert (
        client.delete(
            f"/api/v1/credentials/{credential_id}", headers=headers
        ).status_code
        == 204
    )

    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/credentials", headers=headers).status_code == 401


def test_notes_crud_and_data_persists_after_login(tmp_path):
    client = create_client(tmp_path)
    headers = register(client)
    payload = {"title": "Backup codes", "content": "code-01\ncode-02"}

    created = client.post("/api/v1/notes", json=payload, headers=headers)
    assert created.status_code == 201
    note_id = created.json()["id"]
    client.post("/api/v1/auth/logout", headers=headers)

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "ANA", "password": "senha-forte"},
    )
    assert login.status_code == 200
    next_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/notes", headers=next_headers).json()[0]["id"] == note_id
    assert (
        client.delete(f"/api/v1/notes/{note_id}", headers=next_headers).status_code
        == 204
    )


def test_users_are_isolated_and_invalid_login_is_generic(tmp_path):
    client = create_client(tmp_path)
    first_headers = register(client, "ana")
    second_headers = register(client, "bia")
    client.post(
        "/api/v1/credentials",
        json={"title": "Privada", "password": "segredo"},
        headers=first_headers,
    )

    assert client.get("/api/v1/credentials", headers=second_headers).json() == []
    invalid = client.post(
        "/api/v1/auth/login",
        json={"username": "ana", "password": "errada"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Usuário ou senha inválidos."


def test_session_expires_and_locks_vault(tmp_path):
    client = create_client(tmp_path)
    headers = register(client)
    token = headers["Authorization"].removeprefix("Bearer ")
    session_manager = client.app.state.sessions
    session = session_manager.get(token)
    session.expires_at = 0

    response = client.get("/api/v1/notes", headers=headers)

    assert response.status_code == 401
    assert session.vault.unlocked is False


def test_duplicate_registration_is_rejected(tmp_path):
    client = create_client(tmp_path)
    register(client)

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "ANA", "password": "outra-senha"},
    )

    assert response.status_code == 409


def test_login_to_malformed_vault_locks_derived_key(tmp_path):
    client = create_client(tmp_path)
    headers = register(client)
    token = headers["Authorization"].removeprefix("Bearer ")
    session = client.app.state.sessions.get(token)
    with session.lock:
        session.vault.save("not valid json")
    client.post("/api/v1/auth/logout", headers=headers)

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "ana", "password": "senha-forte"},
    )

    assert response.status_code == 422
    assert session.vault.unlocked is False
    assert session.authenticator.security.unlocked is False


def test_vault_summary_and_search_never_return_credential_secrets(tmp_path):
    client = create_client(tmp_path)
    headers = register(client)
    client.post(
        "/api/v1/credentials",
        json={
            "title": "Email pessoal",
            "username": "ana@example.com",
            "password": "segredo-que-nao-pode-aparecer",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/notes",
        json={"title": "Viagem", "content": "Reserva hotel"},
        headers=headers,
    )

    summary = client.get("/api/v1/vault/summary", headers=headers)
    results = client.get("/api/v1/search?q=email", headers=headers)

    assert summary.json() == {
        "username": "ana",
        "credential_count": 1,
        "note_count": 1,
    }
    assert results.status_code == 200
    assert results.json()[0]["title"] == "Email pessoal"
    assert "password" not in results.text
    assert "segredo-que-nao-pode-aparecer" not in results.text


def test_search_rejects_whitespace_only_query(tmp_path):
    client = create_client(tmp_path)
    headers = register(client)

    response = client.get("/api/v1/search?q=%20%20", headers=headers)

    assert response.status_code == 422
