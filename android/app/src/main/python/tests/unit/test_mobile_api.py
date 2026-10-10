import json

from info_storage.mobile_api import InfoStorageApp


def test_load_integrity_failure_requires_login(tmp_path):
    app = InfoStorageApp(str(tmp_path))
    app.register_json("123456")
    app.create_vault_json("123456")

    content = app.vault_path.read_bytes()
    app.vault_path.write_bytes(content[:-1] + bytes([content[-1] ^ 1]))

    result = json.loads(app.load_data_json())

    assert result["success"] is False
    assert result["requires_login"] is True
    assert app.authenticator.authenticated is False
    assert app.vault.unlocked is False
    assert app.authenticator.security.unlocked is False
