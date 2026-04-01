import sqlite3
from pathlib import Path

from flask import current_app, g, has_app_context

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pharmacy.db"


def resolve_db_path() -> Path:
    try:
        return Path(current_app.config.get("DB_PATH", DEFAULT_DB_PATH))
    except RuntimeError:
        return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    db = g.get("db") if has_app_context() else None
    if db is None:
        db_path = resolve_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON;")
        if has_app_context():
            g.db = db
    return db


def close_db(_=None) -> None:
    db = g.pop("db", None) if has_app_context() else None
    if db is not None:
        db.close()


def init_db() -> None:
    conn = sqlite3.connect(resolve_db_path())
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'pharmacist', 'staff')),
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            UNIQUE(tenant_id, username)
        );

        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            name TEXT NOT NULL,
            generic_composition TEXT,
            brand TEXT,
            manufacturer TEXT,
            batch_no TEXT NOT NULL,
            mfg_date TEXT NOT NULL,
            exp_date TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            rate REAL NOT NULL CHECK(rate >= 0),
            label_notes TEXT,
            code_value TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            UNIQUE(tenant_id, name, batch_no),
            UNIQUE(tenant_id, code_value)
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            sale_date TEXT NOT NULL,
            customer_name TEXT,
            payment_mode TEXT NOT NULL CHECK(payment_mode IN ('cash', 'online')),
            total_amount REAL NOT NULL CHECK(total_amount >= 0),
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            medicine_id INTEGER NOT NULL,
            strips_sold INTEGER NOT NULL DEFAULT 0 CHECK(strips_sold >= 0),
            tablets_sold INTEGER NOT NULL DEFAULT 0 CHECK(tablets_sold >= 0),
            unit_rate REAL NOT NULL CHECK(unit_rate >= 0),
            line_total REAL NOT NULL CHECK(line_total >= 0),
            FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
            FOREIGN KEY(medicine_id) REFERENCES medicines(id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            actor_user_id INTEGER,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER,
            payload_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(actor_user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS api_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL DEFAULT 1,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            duration_ms REAL NOT NULL,
            request_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        );

        CREATE INDEX IF NOT EXISTS idx_sales_sale_date ON sales(sale_date);
        CREATE INDEX IF NOT EXISTS idx_sales_tenant_sale_date ON sales(tenant_id, sale_date);
        CREATE INDEX IF NOT EXISTS idx_medicines_tenant_name ON medicines(tenant_id, name);
        CREATE INDEX IF NOT EXISTS idx_medicines_tenant_batch_no ON medicines(tenant_id, batch_no);
        CREATE INDEX IF NOT EXISTS idx_api_tokens_tenant_user ON api_tokens(tenant_id, user_id);
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO tenants (id, name, code, is_active) VALUES (1, 'Default Tenant', 'default', 1)"
    )
    conn.execute("DROP VIEW IF EXISTS short_list")
    conn.execute(
        """
        CREATE VIEW IF NOT EXISTS short_list AS
        SELECT *
        FROM medicines
        WHERE quantity <= 3
        """
    )
    conn.commit()
    conn.close()
