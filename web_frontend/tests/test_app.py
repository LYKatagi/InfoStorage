import re

from web_frontend.app import create_app


class FakeAPI:
    token = "server-only-bearer-token"
    credentials = []
    notes = []

    def __init__(self, base_url):
        self.base_url = base_url

    def register(self, username, password):
        return {"access_token": self.token, "expires_in": 600, "username": username}

    def login(self, username, password):
        return {"access_token": self.token, "expires_in": 600, "username": username}

    def logout(self, token):
        assert token == self.token

    def summary(self, token):
        assert token == self.token
        return {
            "username": "ana",
            "credential_count": len(self.credentials),
            "note_count": len(self.notes),
        }

    def list_credentials(self, token):
        return self.credentials

    def list_notes(self, token):
        return self.notes

    def search(self, token, query):
        return []

    def create_credential(self, token, values):
        self.credentials.append({"id": "credential-1", **values})

    def delete_credential(self, token, credential_id):
        self.credentials = [
            item for item in self.credentials if item["id"] != credential_id
        ]

    def create_note(self, token, values):
        self.notes.append({"id": "note-1", **values})

    def delete_note(self, token, note_id):
        self.notes = [item for item in self.notes if item["id"] != note_id]


def csrf_token(response):
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match
    return match.group(1).decode()


def make_client(monkeypatch):
    FakeAPI.credentials = []
    FakeAPI.notes = []
    monkeypatch.setattr("web_frontend.app.InfoStorageAPI", FakeAPI)
    app = create_app(api_url="http://api.test", secret_key="test-key")
    app.config.update(TESTING=True)
    return app.test_client()


def test_register_keeps_bearer_token_out_of_cookie_and_renders_dashboard(monkeypatch):
    client = make_client(monkeypatch)
    response = client.get("/register")
    token = csrf_token(response)

    response = client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": "ana",
            "password": "senha-forte",
            "confirmation": "senha-forte",
        },
    )

    assert response.status_code == 302
    cookie = response.headers["Set-Cookie"]
    assert FakeAPI.token not in cookie
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert b"Seu espa\xc3\xa7o seguro" in dashboard.data


def test_dashboard_forms_send_operations_to_api(monkeypatch):
    client = make_client(monkeypatch)
    token = csrf_token(client.get("/login"))
    client.post(
        "/login",
        data={"csrf_token": token, "username": "ana", "password": "senha"},
    )

    dashboard = client.get("/dashboard")
    token = csrf_token(dashboard)
    created = client.post(
        "/credentials",
        data={
            "csrf_token": token,
            "title": "Email",
            "username": "ana@example.com",
            "password": "segredo",
            "notes": "",
        },
    )

    assert created.status_code == 302
    dashboard = client.get("/dashboard")
    assert b"Email" in dashboard.data
    assert b"segredo" in dashboard.data


def test_post_without_csrf_token_is_rejected(monkeypatch):
    client = make_client(monkeypatch)

    response = client.post("/login", data={"username": "ana", "password": "senha"})

    assert response.status_code == 400
