from pathlib import Path

from info_storage.storage.dat import DatStorage
from info_storage.storage.json import JSONStorage


class Storage:
    def __init__(self):
        self.backends = {
            "json": JSONStorage(),
            "dat": DatStorage()
        }

    def get_backend(self, storage_type):
        try:
            return self.backends[storage_type]
        except KeyError as error:
            raise ValueError(
                "Tipo de armazenamento não suportado: "
                + storage_type
            ) from error

    def save(self, file_path, data, storage_type=None):
        file_path = Path(file_path)

        if storage_type is None:
            storage_type = file_path.suffix.removeprefix(".")

        backend = self.get_backend(storage_type)

        backend.save(file_path, data)

    def load(self, file_path, storage_type=None):
        file_path = Path(file_path)

        if storage_type is None:
            storage_type = file_path.suffix.removeprefix(".")

        backend = self.get_backend(storage_type)

        return backend.load(file_path)