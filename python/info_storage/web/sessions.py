import hashlib
import secrets
from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from info_storage.auth.authenticator import Authenticator
from info_storage.vault.vault import Vault


class SessionExpiredError(Exception):
    pass


@dataclass
class AccountSession:
    username: str
    account_key: str
    authenticator: Authenticator
    vault: Vault
    lock: RLock
    token_digest: str = ""
    expires_at: float = 0


class SessionManager:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, AccountSession] = {}
        self._account_sessions: dict[str, str] = {}
        self._lock = RLock()

    def create(self, session: AccountSession) -> str:
        token = secrets.token_urlsafe(32)
        token_digest = self._digest(token)
        with self._lock:
            previous_digest = self._account_sessions.get(session.account_key)
            previous = self._sessions.pop(previous_digest, None)
            session.token_digest = token_digest
            session.expires_at = monotonic() + self.ttl_seconds
            self._sessions[token_digest] = session
            self._account_sessions[session.account_key] = token_digest
        if previous is not None:
            self._close(previous)
        return token

    def get(self, token: str) -> AccountSession:
        token_digest = self._digest(token)
        expired = None
        with self._lock:
            session = self._sessions.get(token_digest)
            if session is None:
                raise SessionExpiredError
            if session.expires_at <= monotonic():
                expired = self._remove(token_digest)
            else:
                session.expires_at = monotonic() + self.ttl_seconds
        if expired is not None:
            self._close(expired)
            raise SessionExpiredError
        return session

    def revoke(self, session: AccountSession) -> None:
        with self._lock:
            removed = self._remove(session.token_digest)
        if removed is not None:
            self._close(removed)

    def _remove(self, token_digest: str) -> AccountSession | None:
        session = self._sessions.pop(token_digest, None)
        if session is not None:
            self._account_sessions.pop(session.account_key, None)
        return session

    @staticmethod
    def _close(session: AccountSession) -> None:
        with session.lock:
            session.vault.lock()
            if session.authenticator.authenticated:
                session.authenticator.logout()

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_session(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AccountSession:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tá tentando entrar sem autenticação em, estranho em 😒",
            headers={"WWW-Authenticate": "Bearer"},
        )

    manager: SessionManager = request.app.state.sessions
    try:
        session = manager.get(credentials.credentials)
        with session.lock:
            session.vault.check_timeout()
    except SessionExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Eu acho que você não foi pelo site real em, to de olho, ou se vc é um dev, blz. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception as error:
        manager.revoke(session)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vixi, o cofre ficou bloqueado, não fica bravo não, é só pros hackers não pegarem seu histórico no chat gpt. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    request.state.account_session = session
    return session


SessionDependency = Annotated[AccountSession, Depends(get_current_session)]
