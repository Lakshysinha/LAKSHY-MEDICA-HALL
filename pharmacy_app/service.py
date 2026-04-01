from datetime import date

from flask import has_app_context

from .db import get_connection
from .tenant import get_tenant_id


class ValidationError(Exception):
    pass


def _finalize_connection(conn):
    if not has_app_context():
        conn.close()


def add_medicine(payload: dict, tenant_id: int | None = None) -> int:
    if payload["exp_date"] <= payload["mfg_date"]:
        raise ValidationError("EXP date must be greater than MFG date")
    tenant_id = tenant_id or get_tenant_id()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO medicines (
                tenant_id, name, generic_composition, brand, manufacturer, batch_no, mfg_date,
                exp_date, quantity, rate, label_notes, code_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                payload["name"],
                payload.get("generic_composition", ""),
                payload.get("brand", ""),
                payload.get("manufacturer", ""),
                payload["batch_no"],
                payload["mfg_date"],
                payload["exp_date"],
                int(payload["quantity"]),
                float(payload["rate"]),
                payload.get("label_notes", ""),
                payload.get("code_value", None),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        _finalize_connection(conn)


def search_medicines(query: str, tenant_id: int | None = None):
    tenant_id = tenant_id or get_tenant_id()
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT * FROM medicines
            WHERE tenant_id = ?
            AND (name LIKE ? OR batch_no LIKE ? OR code_value = ?)
            ORDER BY name
            """,
            (tenant_id, f"%{query}%", f"%{query}%", query),
        ).fetchall()
    finally:
        _finalize_connection(conn)


def get_short_list(tenant_id: int | None = None):
    tenant_id = tenant_id or get_tenant_id()
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM short_list WHERE tenant_id = ? ORDER BY quantity ASC, name ASC", (tenant_id,)
        ).fetchall()
    finally:
        _finalize_connection(conn)


def create_sale(*, medicine_id: int, strips_sold: int, tablets_sold: int, payment_mode: str, customer_name: str = "", user_id: int | None = None, tenant_id: int | None = None):
    total_units = strips_sold + tablets_sold
    if total_units <= 0:
        raise ValidationError("Sold quantity must be greater than zero")
    if payment_mode not in {"cash", "online"}:
        raise ValidationError("Payment mode required")

    tenant_id = tenant_id or get_tenant_id()
    conn = get_connection()
    try:
        med = conn.execute(
            "SELECT * FROM medicines WHERE id = ? AND tenant_id = ?", (medicine_id, tenant_id)
        ).fetchone()
        if not med:
            raise ValidationError("Medicine not found")
        if total_units > med["quantity"]:
            raise ValidationError("Sold quantity cannot exceed available stock")

        line_total = total_units * med["rate"]
        sale_date = date.today().isoformat()
        cur = conn.execute(
            "INSERT INTO sales (tenant_id, sale_date, customer_name, payment_mode, total_amount, created_by) VALUES (?, ?, ?, ?, ?, ?)",
            (tenant_id, sale_date, customer_name, payment_mode, line_total, user_id),
        )
        sale_id = cur.lastrowid
        conn.execute(
            """
            INSERT INTO sale_items (sale_id, medicine_id, strips_sold, tablets_sold, unit_rate, line_total)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sale_id, medicine_id, strips_sold, tablets_sold, med["rate"], line_total),
        )
        conn.execute(
            "UPDATE medicines SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tenant_id = ?",
            (total_units, medicine_id, tenant_id),
        )
        conn.commit()
        return sale_id
    finally:
        _finalize_connection(conn)


def daily_summary(day: str | None = None, tenant_id: int | None = None):
    if not day:
        day = date.today().isoformat()
    tenant_id = tenant_id or get_tenant_id()
    conn = get_connection()
    try:
        totals = conn.execute(
            """
            SELECT
                COALESCE(SUM(si.strips_sold + si.tablets_sold), 0) AS medicines_sold,
                COALESCE(SUM(s.total_amount), 0) AS total_sales,
                COALESCE(SUM(CASE WHEN s.payment_mode = 'cash' THEN s.total_amount ELSE 0 END), 0) AS cash_total,
                COALESCE(SUM(CASE WHEN s.payment_mode = 'online' THEN s.total_amount ELSE 0 END), 0) AS online_total
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
            WHERE s.sale_date = ? AND s.tenant_id = ?
            """,
            (day, tenant_id),
        ).fetchone()
        sales = conn.execute(
            """
            SELECT s.*, m.name AS medicine_name, si.strips_sold, si.tablets_sold, si.unit_rate, si.line_total
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN medicines m ON m.id = si.medicine_id
            WHERE s.sale_date = ? AND s.tenant_id = ?
            ORDER BY s.id DESC
            """,
            (day, tenant_id),
        ).fetchall()
        return totals, sales
    finally:
        _finalize_connection(conn)
