from info_storage.auth import Authenticator
from info_storage.main import app


def test_menu_offers_login_when_credentials_exist(tmp_path, monkeypatch, capsys):
    credentials_path = tmp_path / "credentials.json"
    Authenticator(credentials_path).register("123456")
    monkeypatch.setattr(app, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(app, "CREDENTIALS_FILE", credentials_path)
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app.main()

    menu = capsys.readouterr().out
    assert "1. Login" in menu
    assert "Criar conta" not in menu


def test_menu_offers_account_creation_without_credentials(
    tmp_path, monkeypatch, capsys
):
    credentials_path = tmp_path / "credentials.json"
    monkeypatch.setattr(app, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(app, "CREDENTIALS_FILE", credentials_path)
    monkeypatch.setattr("builtins.input", lambda _: "0")

    app.main()

    menu = capsys.readouterr().out
    assert "1. Criar conta" in menu
    assert "1. Login" not in menu
