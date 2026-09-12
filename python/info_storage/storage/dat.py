from pathlib import Path


class DatStorage:
    def save(self, file_path, data):
        file_path = Path(file_path)

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if isinstance(data, str):
            data = data.encode("utf-8")

        with file_path.open("wb") as file:
            file.write(data)

    def load(self, file_path):
        file_path = Path(file_path)

        with file_path.open("rb") as file:
            return file.read()