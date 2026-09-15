import pytest

from info_storage.auth.credentials import Credentials


def test_create_credentials(tmp_path):
    credentials_path = tmp_path / "credentials.json"

    credentials = Credentials(credentials_path)

    credentials.create("123456")

    assert credentials_path.exists()


def test_verify_correct_password(tmp_path):
    credentials_path = tmp_path / "credentials.json"

    credentials = Credentials(credentials_path)

    credentials.create("123456")

    assert credentials.verify("123456") is True


def test_verify_wrong_password(tmp_path):
    credentials_path = tmp_path / "credentials.json"

    credentials = Credentials(credentials_path)

    credentials.create("123456")

    assert credentials.verify("senha-errada") is False


def test_credentials_already_exist(tmp_path):
    credentials_path = tmp_path / "credentials.json"

    credentials = Credentials(credentials_path)

    credentials.create("123456")

    with pytest.raises(FileExistsError):
        credentials.create("654321")


def test_credentials_file_not_found(tmp_path):
    credentials_path = tmp_path / "credentials.json"

    credentials = Credentials(credentials_path)

    with pytest.raises(FileNotFoundError):
        credentials.verify("123456")


def test_empty_password(tmp_path):
    credentials_path = tmp_path / "credentials.json"

    credentials = Credentials(credentials_path)

    with pytest.raises(ValueError):
        credentials.create("")


def test_password_is_not_saved(tmp_path):
    credentials_path = tmp_path / "credentials.json"

    credentials = Credentials(credentials_path)

    credentials.create("123456")

    content = credentials_path.read_text(encoding="utf-8")

    assert "123456" not in content
    assert "password_hash" in content
