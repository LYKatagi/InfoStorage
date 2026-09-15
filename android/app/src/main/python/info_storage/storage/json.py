import json
from pathlib import Path


class JSONStorage:
    def save(self, file_path, data):
        file_path = Path(file_path)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load(self, file_path):
        file_path = Path(file_path)

        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
