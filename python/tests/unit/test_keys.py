import pytest

from info_storage.security.keys import SecurityManager


def test_setup_generates_salt():
    security = SecurityManager()

    salt = security.setup("senha segura")

    assert salt is not None
    assert isinstance(salt, bytes)
    assert len(salt) == 16


def test_setup_generates_key():
    security = SecurityManager()

    security.setup("senha segura")

    assert security.key is not None
    assert isinstance(security.key, bytes)
    assert len(security.key) == 44


def test_encrypt_and_decrypt():
    security = SecurityManager()

    security.setup("senha segura")

    original_data = "Minha informação secreta"

    encrypted_data = security.encrypt(original_data)
    decrypted_data = security.decrypt(encrypted_data)

    assert decrypted_data == original_data
    assert encrypted_data != original_data


def test_different_passwords_generate_different_keys():
    security_one = SecurityManager()
    security_two = SecurityManager()

    security_one.setup("senha um")
    security_two.setup("senha dois")

    assert security_one.key != security_two.key


def test_same_password_and_salt_generate_same_key():
    security_one = SecurityManager()
    security_two = SecurityManager()

    salt = security_one.setup("senha segura")

    security_two.unlock("senha segura", salt)

    assert security_one.key == security_two.key


def test_wrong_password_cannot_decrypt():
    security_one = SecurityManager()
    security_two = SecurityManager()

    salt = security_one.setup("senha correta")
    encrypted_data = security_one.encrypt("Informação secreta")

    security_two.unlock("senha errada", salt)

    with pytest.raises(ValueError):
        security_two.decrypt(encrypted_data)


def test_modified_data_cannot_be_decrypted():
    security = SecurityManager()

    security.setup("senha segura")

    encrypted_data = security.encrypt("Informação secreta")

    modified_data = encrypted_data[:-1] + b"x"

    with pytest.raises(ValueError):
        security.decrypt(modified_data)


def test_cannot_encrypt_before_setup():
    security = SecurityManager()

    with pytest.raises(RuntimeError):
        security.encrypt("teste")


def test_cannot_decrypt_before_setup():
    security = SecurityManager()

    with pytest.raises(RuntimeError):
        security.decrypt(b"invalid-token")


def test_empty_string():
    security = SecurityManager()

    security.setup("senha segura")

    encrypted_data = security.encrypt("")
    decrypted_data = security.decrypt(encrypted_data)

    assert decrypted_data == ""


def test_unicode_text():
    security = SecurityManager()

    security.setup("senha segura")

    original_data = "Informação com acentuação: çãõ 🔐"

    encrypted_data = security.encrypt(original_data)
    decrypted_data = security.decrypt(encrypted_data)

    assert decrypted_data == original_data