from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from info_storage.web.schemas import AuthRequest, MessageResponse, SessionResponse
from info_storage.web.sessions import (
    SessionDependency,
)
from info_storage.web.storage import (
    AccountAlreadyExistsError,
    InvalidLoginError,
    InvalidVaultDataError,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])
limiter = Limiter(get_remote_address)
@router.post(
    "/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)

def register(body: AuthRequest, request: Request) -> SessionResponse:
    store = request.app.state.account_store
    try:
        session = store.register(body.username, body.password)
    except AccountAlreadyExistsError:
        raise HTTPException(
            status_code=409, detail="Nome de usuário indisponível."
        ) from None
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Senha inválida.") from None

    token = request.app.state.sessions.create(session)
    return SessionResponse(
        access_token=token,
        expires_in=request.app.state.settings.session_ttl_seconds,
        username=session.username,
    )


@router.post("/login", response_model=SessionResponse)
def login(body: AuthRequest, request: Request) -> SessionResponse:
    store = request.app.state.account_store
    try:
        session = store.login(body.username, body.password)
    except InvalidLoginError:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except InvalidVaultDataError:
        raise HTTPException(
            status_code=422, detail="O cofre está inválido ou corrompido."
        ) from None

    token = request.app.state.sessions.create(session)
    return SessionResponse(
        access_token=token,
        expires_in=request.app.state.settings.session_ttl_seconds,
        username=session.username,
    )


@router.get("/me")
def current_user(
    session: SessionDependency,
) -> dict[str, str]:
    return {"username": session.username}


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    session: SessionDependency,
) -> MessageResponse:
    request.app.state.sessions.revoke(session)
    return MessageResponse(message="Sessão encerrada.")
