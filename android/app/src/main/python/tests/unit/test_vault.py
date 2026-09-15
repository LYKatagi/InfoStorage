import pytest

from info_storage.vault.exceptions import (
    IntegrityError,
    InvalidVaultError,
    VaultAlreadyExistsError,
    VaultLockedError,
)
from info_storage.vault.vault import Vault


def test_create_vault(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")

    assert vault_path.exists()
    assert vault.unlocked is True


def test_unlock_vault(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")
    vault.lock()

    data = vault.unlock("123456")

    assert data == "dados secretos"
    assert vault.unlocked is True


def test_wrong_password(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")
    vault.lock()

    with pytest.raises(IntegrityError):
        vault.unlock("senha-errada")


def test_existing_vault(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")

    with pytest.raises(VaultAlreadyExistsError):
        vault.create("654321", "outros dados")


def test_save_locked_vault(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")
    vault.lock()

    with pytest.raises(VaultLockedError):
        vault.save("novos dados")


def test_load_locked_vault(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")
    vault.lock()

    with pytest.raises(VaultLockedError):
        vault.load()


def test_lock_vault(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")
    vault.lock()

    assert vault.unlocked is False


def test_save_and_load_data(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados antigos")
    vault.save("dados novos")

    assert vault.load() == "dados novos"


def test_vault_format(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")

    content = vault_path.read_bytes()
    parts = content.split(b"\n", maxsplit=4)

    assert len(parts) == 5
    assert parts[0] == b"INFOSTORAGE"
    assert parts[1] == b"2"
    assert len(parts[2]) == 32
    assert len(parts[3]) == 64
    assert len(parts[4]) > 0


def test_invalid_vault_structure(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault_path.write_bytes(b"arquivo invalido")

    vault = Vault(vault_path)

    with pytest.raises(InvalidVaultError):
        vault.unlock("123456")


def test_invalid_magic(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")

    content = vault_path.read_bytes()
    content = content.replace(
        b"INFOSTORAGE",
        b"INVALID____",
    )

    vault_path.write_bytes(content)
    vault.lock()

    with pytest.raises(InvalidVaultError):
        vault.unlock("123456")


def test_invalid_version(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")

    content = vault_path.read_bytes()
    content = content.replace(b"\n2\n", b"\n99\n")

    vault_path.write_bytes(content)
    vault.lock()

    with pytest.raises(InvalidVaultError):
        vault.unlock("123456")


def test_integrity_failure(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")

    content = vault_path.read_bytes()
    content = content[:-1] + bytes([content[-1] ^ 1])

    vault_path.write_bytes(content)
    vault.lock()

    with pytest.raises(IntegrityError):
        vault.unlock("123456")


def test_integrity_signature_modified(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")

    content = vault_path.read_bytes()
    parts = content.split(b"\n", maxsplit=4)

    signature = parts[3]

    replacement = b"1" if signature[:1] == b"0" else b"0"

    parts[3] = replacement + signature[1:]

    modified_content = b"\n".join(parts)

    vault_path.write_bytes(modified_content)
    vault.lock()

    with pytest.raises(IntegrityError):
        vault.unlock("123456")


def test_integrity_success(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados secretos")
    vault.lock()

    data = vault.unlock("123456")

    assert data == "dados secretos"


def test_save_updates_integrity(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path)

    vault.create("123456", "dados antigos")
    vault.save("dados novos")
    vault.lock()

    data = vault.unlock("123456")

    assert data == "dados novos"


def test_timeout_locks_vault(tmp_path):
    vault_path = tmp_path / "vault.dat"
    vault = Vault(vault_path, timeout=1)

    vault.create("123456", "dados secretos")

    vault.timer._last_activity = vault.timer._last_activity - 2.0

    with pytest.raises(VaultLockedError):
        vault.load()

    assert vault.unlocked is False
