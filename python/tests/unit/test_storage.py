import json

import pytest

from info_storage.storage.dat import DatStorage
from info_storage.storage.json import JSONStorage
from info_storage.storage.storage import Storage


def test_json_storage_save_and_load(tmp_path):
    storage = JSONStorage()

    file_path = tmp_path / "data.json"

    data = {"name": "GitHub", "username": "luiz", "active": True}

    storage.save(file_path, data)

    assert file_path.exists()

    loaded_data = storage.load(file_path)

    assert loaded_data == data


def test_json_storage_supports_unicode(tmp_path):
    storage = JSONStorage()

    file_path = tmp_path / "data.json"

    data = {"message": "Informação com acentuação", "emoji": "🔐"}

    storage.save(file_path, data)

    loaded_data = storage.load(file_path)

    assert loaded_data == data


def test_json_storage_creates_parent_directory(tmp_path):
    storage = JSONStorage()

    file_path = tmp_path / "nested" / "folder" / "data.json"

    storage.save(file_path, {"test": True})

    assert file_path.exists()
    assert storage.load(file_path) == {"test": True}


def test_json_storage_file_contains_valid_json(tmp_path):
    storage = JSONStorage()

    file_path = tmp_path / "data.json"

    data = {"version": 1, "items": ["one", "two"]}

    storage.save(file_path, data)

    with file_path.open("r", encoding="utf-8") as file:
        loaded_data = json.load(file)

    assert loaded_data == data


def test_json_storage_missing_file(tmp_path):
    storage = JSONStorage()

    file_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        storage.load(file_path)


def test_dat_storage_save_and_load_bytes(tmp_path):
    storage = DatStorage()

    file_path = tmp_path / "data.dat"

    data = b"\x00\x01\x02\xff\xfe"

    storage.save(file_path, data)

    assert file_path.exists()

    loaded_data = storage.load(file_path)

    assert loaded_data == data


def test_dat_storage_save_and_load_string(tmp_path):
    storage = DatStorage()

    file_path = tmp_path / "data.dat"

    data = "Informação secreta"

    storage.save(file_path, data)

    loaded_data = storage.load(file_path)

    assert loaded_data == data.encode("utf-8")


def test_dat_storage_creates_parent_directory(tmp_path):
    storage = DatStorage()

    file_path = tmp_path / "nested" / "data.dat"

    storage.save(file_path, b"data")

    assert file_path.exists()
    assert storage.load(file_path) == b"data"


def test_dat_storage_missing_file(tmp_path):
    storage = DatStorage()

    file_path = tmp_path / "missing.dat"

    with pytest.raises(FileNotFoundError):
        storage.load(file_path)


def test_storage_uses_json_backend(tmp_path):
    storage = Storage()

    file_path = tmp_path / "data.json"

    data = {"app": "InfoStorage", "version": 1}

    storage.save(file_path, data)

    assert storage.load(file_path) == data


def test_storage_uses_dat_backend(tmp_path):
    storage = Storage()

    file_path = tmp_path / "data.dat"

    data = b"binary data"

    storage.save(file_path, data)

    assert storage.load(file_path) == data


def test_storage_manual_backend_selection(tmp_path):
    storage = Storage()

    file_path = tmp_path / "file_without_extension"

    data = {"selected": "json"}

    storage.save(file_path, data, storage_type="json")

    assert storage.load(file_path, storage_type="json") == data


def test_storage_unsupported_backend(tmp_path):
    storage = Storage()

    file_path = tmp_path / "data.unknown"

    with pytest.raises(ValueError):
        storage.save(file_path, {"test": True})


def test_storage_unsupported_load_backend(tmp_path):
    storage = Storage()

    file_path = tmp_path / "data.unknown"

    with pytest.raises(ValueError):
        storage.load(file_path)
