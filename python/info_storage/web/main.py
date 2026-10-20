from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from info_storage.vault.exceptions import VaultError, VaultLockedError
from info_storage.web.config import Settings
from info_storage.web.routes import auth, credentials, notes, passwords, vault
from info_storage.web.sessions import SessionManager
from info_storage.web.storage import AccountStore, InvalidVaultDataError


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_environment()
    if settings.session_ttl_seconds < 60:
        raise ValueError("A duração da sessão deve ser de pelo menos 60 segundos.")

    app = FastAPI(
        title="InfoStorage API",
        description="API autenticada para credenciais e notas protegidas pelo vault InfoStorage. e um toquinho de humor",
        version="1.0.0",
    )
    app.state.settings = settings
    app.state.account_store = AccountStore(
        settings.data_dir, settings.session_ttl_seconds
    )
    app.state.sessions = SessionManager(settings.session_ttl_seconds)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(credentials.router, prefix="/api/v1")
    app.include_router(notes.router, prefix="/api/v1")
    app.include_router(passwords.router, prefix="/api/v1")
    app.include_router(vault.router, prefix="/api/v1")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(VaultError)
    async def handle_vault_error(request: Request, error: VaultError):
        session = getattr(request.state, "account_session", None)
        if session is not None:
            app.state.sessions.revoke(session)
        if isinstance(error, VaultLockedError):
            return JSONResponse(
                status_code=401,
                headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
                content={"detail": "Cofre bloqueado pq tu demorou demais. Faça login novamente."},
            )
        return JSONResponse(
            status_code=422,
            content={"detail": "O cofre está inválido ou sua integridade falhou. seu dados foram perdidos, YEY!!!"},
        )

    @app.exception_handler(InvalidVaultDataError)
    async def handle_invalid_vault_data(request: Request, error: InvalidVaultDataError):
        session = getattr(request.state, "account_session", None)
        if session is not None:
            app.state.sessions.revoke(session)
        return JSONResponse(
            status_code=422,
            content={"detail": "Os dados do cofre estão inválidos, puts, vc lembra suas senhas?"},
        )

    @app.get("/health", tags=["Sistema"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
