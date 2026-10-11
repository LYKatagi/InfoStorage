import hmac
import os
import secrets
from collections.abc import Callable
from contextlib import suppress
from datetime import timedelta
from functools import wraps
from typing import Any

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from web_frontend.api_client import APIError, InfoStorageAPI
from web_frontend.sessions import FrontendSessionStore


def create_app(
    api_url: str | None = None,
    secret_key: str | None = None,
    session_store: FrontendSessionStore | None = None,
) -> Flask:
    app = Flask(__name__)
    app.secret_key = (
        secret_key or os.getenv("INFOSTORAGE_FLASK_SECRET") or secrets.token_hex(32)
    )
    app.config.update(
        API_URL=api_url or os.getenv("INFOSTORAGE_API_URL", "http://127.0.0.1:8000"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("INFOSTORAGE_COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    app.extensions["web_sessions"] = session_store or FrontendSessionStore()

    def api() -> InfoStorageAPI:
        return InfoStorageAPI(app.config["API_URL"])

    def clear_frontend_session() -> None:
        session_store = app.extensions["web_sessions"]
        session_store.remove(session.get("web_session_id"))
        session.clear()

    def login_required(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any):
            if g.frontend_session is None:
                flash("Sua sessão expirou. Entre novamente.", "error")
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped

    @app.before_request
    def load_session_and_check_csrf() -> None:
        session.permanent = True
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)

        session_id = session.get("web_session_id")
        g.frontend_session = app.extensions["web_sessions"].get(session_id)
        if session_id and g.frontend_session is None:
            session.pop("web_session_id", None)

        if request.method == "POST":
            expected = session.get("csrf_token", "")
            provided = request.form.get("csrf_token", "")
            if not expected or not hmac.compare_digest(expected, provided):
                abort(400, description="Token CSRF inválido.")

    @app.after_request
    def add_security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        return response

    @app.context_processor
    def inject_template_values() -> dict[str, Any]:
        return {
            "csrf_token": session.get("csrf_token", ""),
            "current_user": (
                g.frontend_session.username if g.frontend_session is not None else None
            ),
        }

    def handle_api_error(error: APIError):
        if error.status_code == 401:
            clear_frontend_session()
            flash("Sua sessão expirou. Entre novamente.", "error")
            return redirect(url_for("login"))
        flash(error.detail, "error")
        return redirect(request.referrer or url_for("dashboard"))

    @app.get("/")
    def index():
        if g.frontend_session is not None:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or not password:
                flash("Informe usuário e senha.", "error")
            else:
                try:
                    data = api().login(username, password)
                    clear_frontend_session()
                    session_id = secrets.token_urlsafe(32)
                    app.extensions["web_sessions"].create(
                        session_id,
                        data["username"],
                        data["access_token"],
                        int(data["expires_in"]),
                    )
                    session["web_session_id"] = session_id
                    session.permanent = True
                    flash("Cofre desbloqueado.", "success")
                    return redirect(url_for("dashboard"))
                except APIError as error:
                    flash(error.detail, "error")
        return render_template("auth.html", mode="login")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirmation = request.form.get("confirmation", "")
            if password != confirmation:
                flash("As senhas não coincidem.", "error")
            elif not username or not password:
                flash("Informe usuário e senha.", "error")
            else:
                try:
                    data = api().register(username, password)
                    clear_frontend_session()
                    session_id = secrets.token_urlsafe(32)
                    app.extensions["web_sessions"].create(
                        session_id,
                        data["username"],
                        data["access_token"],
                        int(data["expires_in"]),
                    )
                    session["web_session_id"] = session_id
                    session.permanent = True
                    flash("Conta criada e cofre pronto.", "success")
                    return redirect(url_for("dashboard"))
                except APIError as error:
                    flash(error.detail, "error")
        return render_template("auth.html", mode="register")

    @app.get("/dashboard")
    @login_required
    def dashboard():
        api_session = g.frontend_session
        try:
            summary = api().summary(api_session.api_token)
            credentials = api().list_credentials(api_session.api_token)
            notes = api().list_notes(api_session.api_token)
            query = request.args.get("q", "").strip()
            results = (
                api().search(api_session.api_token, query) if len(query) >= 2 else []
            )
        except APIError as error:
            return handle_api_error(error)
        return render_template(
            "dashboard.html",
            summary=summary,
            credentials=credentials,
            notes=notes,
            query=query,
            results=results,
        )

    @app.post("/credentials")
    @login_required
    def create_credential():
        values = {
            "title": request.form.get("title", "").strip(),
            "username": request.form.get("username", "").strip(),
            "password": request.form.get("password", ""),
            "notes": request.form.get("notes", "").strip(),
        }
        try:
            api().create_credential(g.frontend_session.api_token, values)
            flash("Credencial salva no cofre.", "success")
        except APIError as error:
            return handle_api_error(error)
        return redirect(url_for("dashboard"))

    @app.post("/credentials/<credential_id>/delete")
    @login_required
    def delete_credential(credential_id: str):
        try:
            api().delete_credential(g.frontend_session.api_token, credential_id)
            flash("Credencial removida.", "success")
        except APIError as error:
            return handle_api_error(error)
        return redirect(url_for("dashboard"))

    @app.post("/notes")
    @login_required
    def create_note():
        values = {
            "title": request.form.get("title", "").strip(),
            "content": request.form.get("content", "").strip(),
        }
        try:
            api().create_note(g.frontend_session.api_token, values)
            flash("Nota salva no cofre.", "success")
        except APIError as error:
            return handle_api_error(error)
        return redirect(url_for("dashboard"))

    @app.post("/notes/<note_id>/delete")
    @login_required
    def delete_note(note_id: str):
        try:
            api().delete_note(g.frontend_session.api_token, note_id)
            flash("Nota removida.", "success")
        except APIError as error:
            return handle_api_error(error)
        return redirect(url_for("dashboard"))

    @app.post("/logout")
    @login_required
    def logout():
        with suppress(APIError):
            api().logout(g.frontend_session.api_token)
        clear_frontend_session()
        flash("Sessão encerrada.", "success")
        return redirect(url_for("login"))

    return app


app = create_app()
