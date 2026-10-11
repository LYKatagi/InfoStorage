from dataclasses import dataclass
from threading import RLock
from time import monotonic


@dataclass
class FrontendSession:
    username: str
    api_token: str
    ttl_seconds: int
    expires_at: float


class FrontendSessionStore:
    def __init__(self):
        self._sessions: dict[str, FrontendSession] = {}
        self._lock = RLock()

    def create(
        self, session_id: str, username: str, api_token: str, expires_in: int
    ) -> None:
        with self._lock:
            self._sessions[session_id] = FrontendSession(
                username=username,
                api_token=api_token,
                ttl_seconds=expires_in,
                expires_at=monotonic() + expires_in,
            )

    def get(self, session_id: str | None) -> FrontendSession | None:
        if not session_id:
            return None
        with self._lock:
            stored = self._sessions.get(session_id)
            if stored is None:
                return None
            if stored.expires_at <= monotonic():
                self._sessions.pop(session_id, None)
                return None
            stored.expires_at = monotonic() + stored.ttl_seconds
            return stored

    def remove(self, session_id: str | None) -> FrontendSession | None:
        if not session_id:
            return None
        with self._lock:
            return self._sessions.pop(session_id, None)
