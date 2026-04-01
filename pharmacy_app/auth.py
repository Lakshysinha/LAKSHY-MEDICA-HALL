import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Callable

from flask import current_app, flash, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_connection
from .tenant import resolve_tenant_code, set_request_tenant


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_tenant_by_code(code: str):
    conn = get_connection()
    return conn.execute("SELECT * FROM tenants WHERE code = ? AND is_active = 1", (code,)).fetchone()
def _get_or_create_default_tenant_id() -> int:
    slug = current_app.config["DEFAULT_TENANT_SLUG"]
    name = current_app.config["DEFAULT_TENANT_NAME"]
    conn = get_connection()
    tenant = conn.execute("SELECT id FROM tenants WHERE slug = ?", (slug,)).fetchone()
    if tenant:
        return tenant["id"]
    cur = conn.execute("INSERT INTO tenants (slug, name) VALUES (?, ?)", (slug, name))
    conn.commit()
    return cur.lastrowid


def ensure_default_owner() -> None:
    username = current_app.config["DEFAULT_OWNER_USERNAME"]
    password = current_app.config["DEFAULT_OWNER_PASSWORD"]
    tenant_code = current_app.config["DEFAULT_TENANT_CODE"]
    tenant_name = current_app.config["DEFAULT_TENANT_NAME"]
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO tenants (name, code, is_active) VALUES (?, ?, 1)",
        (tenant_name, tenant_code),
    )
    tenant = conn.execute("SELECT id FROM tenants WHERE code = ?", (tenant_code,)).fetchone()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? AND tenant_id = ?", (username, tenant["id"])
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (tenant_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            (tenant["id"], username, generate_password_hash(password), "owner"),
        )
    conn.commit()


def authenticate(username: str, password: str):
    tenant_code = resolve_tenant_code()
    tenant = _get_tenant_by_code(tenant_code)
    if not tenant:
        return None
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1 AND tenant_id = ?",
        (username, tenant["id"]),
    ).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        g.tenant = tenant
    tenant_id = _get_or_create_default_tenant_id()
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE tenant_id = ? AND username = ?", (tenant_id, username)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (tenant_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            (tenant_id, username, generate_password_hash(password), "owner"),
def ensure_default_owner() -> None:
    username = current_app.config["DEFAULT_OWNER_USERNAME"]
    password = current_app.config["DEFAULT_OWNER_PASSWORD"]
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), "owner"),
        )
        conn.commit()


def authenticate(username: str, password: str, tenant_slug: str | None = None):
    conn = get_connection()
    tenant_slug = tenant_slug or current_app.config["DEFAULT_TENANT_SLUG"]
    user = conn.execute(
        """
        SELECT u.*, t.slug AS tenant_slug
        FROM users u
        JOIN tenants t ON t.id = u.tenant_id
        WHERE u.username = ? AND u.is_active = 1 AND t.slug = ? AND t.is_active = 1
        """,
        (username, tenant_slug),
    ).fetchone()
def authenticate(username: str, password: str):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def tenant_required(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        tenant = _get_tenant_by_code(resolve_tenant_code())
        if not tenant:
            return {"error": "Unknown tenant"}, 404
        g.tenant = tenant
        return func(*args, **kwargs)

    return wrapper


def login_required(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


def role_required(allowed_roles: set[str]):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                flash("You do not have permission.", "danger")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def issue_api_token(user_id: int, tenant_id: int) -> tuple[str, str]:
def issue_api_token(user_id: int) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = (_utc_now() + timedelta(seconds=current_app.config["API_TOKEN_TTL_SECONDS"])).isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO api_tokens (tenant_id, user_id, token_hash, expires_at) VALUES (?, ?, ?, ?)",
        (tenant_id, user_id, token_hash, expires_at),
        "INSERT INTO api_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expires_at),
    )
    conn.commit()
    return token, expires_at


def revoke_api_token(token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_connection()
    conn.execute(
        "UPDATE api_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
        (_utc_now().isoformat(), token_hash),
    )
    conn.commit()


def api_auth_required(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return {"error": "Missing bearer token"}, 401
        token = auth.split(" ", 1)[1].strip()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        conn = get_connection()
        token_row = conn.execute(
            """
            SELECT at.*, u.username, u.role, u.is_active, t.code AS tenant_code
            FROM api_tokens at
            JOIN users u ON u.id = at.user_id
            JOIN tenants t ON t.id = at.tenant_id
            SELECT at.*, u.username, u.role, u.is_active, u.tenant_id, t.slug AS tenant_slug, t.is_active AS tenant_active
            FROM api_tokens at
            JOIN users u ON u.id = at.user_id
            JOIN tenants t ON t.id = u.tenant_id
            SELECT at.*, u.username, u.role, u.is_active
            FROM api_tokens at
            JOIN users u ON u.id = at.user_id
            WHERE at.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if not token_row:
            return {"error": "Invalid token"}, 401
        if token_row["revoked_at"] is not None:
            return {"error": "Token revoked"}, 401
        if _utc_now() >= datetime.fromisoformat(token_row["expires_at"]):
            return {"error": "Token expired"}, 401
        if token_row["is_active"] != 1 or token_row["tenant_active"] != 1:
            return {"error": "User or tenant inactive"}, 403
        if token_row["is_active"] != 1:
            return {"error": "User inactive"}, 403
        g.api_user = token_row
        g.api_token = token
        set_request_tenant({"id": token_row["tenant_id"], "code": token_row["tenant_code"]})
        return func(*args, **kwargs)

    return wrapper
