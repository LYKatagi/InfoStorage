import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    session_ttl_seconds: int = 900

    @classmethod
    def from_environment(cls) -> "Settings":
        data_dir = Path(
            os.getenv("INFOSTORAGE_WEB_DATA", PROJECT_ROOT / "web" / "data")
        ).expanduser()
        session_ttl = int(os.getenv("INFOSTORAGE_SESSION_TTL", "900"))
        if session_ttl < 60:
            raise ValueError("INFOSTORAGE_SESSION_TTL deve ser pelo menos 60.")
        return cls(data_dir=data_dir, session_ttl_seconds=session_ttl)
