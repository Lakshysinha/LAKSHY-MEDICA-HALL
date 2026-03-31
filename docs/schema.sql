CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('owner', 'pharmacist', 'staff')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id),
    UNIQUE(tenant_id, username)
);

CREATE TABLE medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
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

CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    sale_date TEXT NOT NULL,
    customer_name TEXT,
    payment_mode TEXT NOT NULL CHECK(payment_mode IN ('cash', 'online')),
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id),
    FOREIGN KEY(created_by) REFERENCES users(id)
);

CREATE TABLE sale_items (
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
