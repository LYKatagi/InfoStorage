from pathlib import Path

from info_storage.storage.dat import DatStorage
from info_storage.storage.json import JSONStorage


class Storage:
    def __init__(self):
        self.backends = {"json": JSONStorage(), "dat": DatStorage()}

    def get_backend(self, storage_type):
        try:
            return self.backends[storage_type.lower()]
        except (KeyError, AttributeError) as error:
            raise ValueError(
                "Tipo de armazenamento não suportado: " + str(storage_type)
            ) from error

    def _detect_type(self, file_path):
        suffix = Path(file_path).suffix.lower()

        if not suffix:
            raise ValueError("Não foi possível identificar o tipo do arquivo.")

        return suffix.removeprefix(".")

    def save(self, file_path, data, storage_type=None):
        if storage_type is None:
            storage_type = self._detect_type(file_path)

        backend = self.get_backend(storage_type)

        backend.save(file_path, data)

    def load(self, file_path, storage_type=None):
        if storage_type is None:
            storage_type = self._detect_type(file_path)

        backend = self.get_backend(storage_type)

        return backend.load(file_path)
