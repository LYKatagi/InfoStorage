import pytest

from info_storage.auth import Authenticator

from info_storage.auth.exceptions import (
    AlreadyAuthenticatedError,
    InvalidCredentialsError,
    UserNotAuthenticatedError,
    AlreadyExistsError
)


def create_authenticator(tmp_path):
    credentials_path = (
        tmp_path / "credentials.json"
    )

    return Authenticator(
        credentials_path
    )


def test_register_password(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")

    assert auth.credentials.exists()
    assert auth.authenticated is False


def test_authenticate_correct_password(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")
    auth.authenticate("123456")

    assert auth.authenticated is True


def test_authenticate_wrong_password(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")

    with pytest.raises(InvalidCredentialsError):
        auth.authenticate("senha-errada")


def test_authenticate_without_credentials(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    with pytest.raises(InvalidCredentialsError):
        auth.authenticate("123456")


def test_duplicate_registration(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")

    with pytest.raises(AlreadyExistsError):
        auth.register("654321")


def test_duplicate_authentication(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")
    auth.authenticate("123456")

    with pytest.raises(AlreadyAuthenticatedError):
        auth.authenticate("123456")


def test_logout(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")
    auth.authenticate("123456")
    auth.logout()

    assert auth.authenticated is False


def test_require_authentication(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    with pytest.raises(UserNotAuthenticatedError):
        auth.require_authentication()


def test_require_authentication_after_login(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")
    auth.authenticate("123456")

    auth.require_authentication()

    assert auth.authenticated is True


def test_authentication_persists_in_file(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")

    new_auth = create_authenticator(
        tmp_path
    )

    new_auth.authenticate("123456")

    assert new_auth.authenticated is True


def test_wrong_password_does_not_authenticate(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    auth.register("123456")

    with pytest.raises(InvalidCredentialsError):
        auth.authenticate("senha-errada")

    assert auth.authenticated is False


def test_empty_password_registration(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    with pytest.raises(ValueError):
        auth.register("")


def test_invalid_password_type(tmp_path):
    auth = create_authenticator(
        tmp_path
    )

    with pytest.raises(TypeError):
        auth.register(123456)