import pytest

from info_storage.vault.exceptions import (
    InvalidVaultError,
    VaultAlreadyExistsError,
    VaultLockedError,
)
from info_storage.vault.vault import Vault


def test_create_vault(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    vault.create(
        "senha-forte",
        "informação secreta"
    )

    assert file_path.exists()
    assert vault.unlocked is True


def test_unlock_vault(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    vault.create(
        "senha-forte",
        "informação secreta"
    )

    other_vault = Vault(file_path)

    data = other_vault.unlock("senha-forte")

    assert data == "informação secreta"
    assert other_vault.unlocked is True


def test_wrong_password(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    vault.create(
        "senha-correta",
        "dados privados"
    )

    other_vault = Vault(file_path)

    with pytest.raises(InvalidVaultError):
        other_vault.unlock("senha-errada")


def test_existing_vault_cannot_be_created_again(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    vault.create(
        "senha",
        "dados"
    )

    with pytest.raises(VaultAlreadyExistsError):
        vault.create(
            "outra-senha",
            "novos dados"
        )


def test_locked_vault_cannot_save(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    with pytest.raises(VaultLockedError):
        vault.save("dados")


def test_locked_vault_cannot_load(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    with pytest.raises(VaultLockedError):
        vault.load()


def test_lock_vault(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    vault.create(
        "senha",
        "dados"
    )

    vault.lock()

    assert vault.unlocked is False

    with pytest.raises(VaultLockedError):
        vault.save("novos dados")


def test_save_and_load_data(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    vault.create(
        "senha",
        "dados iniciais"
    )

    vault.save("dados atualizados")

    assert vault.load() == "dados atualizados"


def test_vault_format_is_valid(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(file_path)

    vault.create(
        "senha",
        "dados"
    )

    content = file_path.read_bytes()

    assert content.startswith(b"INFOSTORAGE\n1\n")


def test_invalid_vault_file(tmp_path):
    file_path = tmp_path / "vault.dat"

    file_path.write_bytes(
        b"arquivo-invalido"
    )

    vault = Vault(file_path)

    with pytest.raises(InvalidVaultError):
        vault.unlock("senha")


def test_timer_locks_vault(tmp_path):
    file_path = tmp_path / "vault.dat"

    vault = Vault(
        file_path,
        timeout=0.001
    )

    vault.create(
        "senha",
        "dados"
    )

    import time

    time.sleep(0.01)

    with pytest.raises(VaultLockedError):
        vault.save("novos dados")
