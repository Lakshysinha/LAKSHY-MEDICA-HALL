from datetime import date

from flask import Blueprint, g, request

from .auth import api_auth_required, authenticate, issue_api_token, revoke_api_token
from .service import ValidationError, add_medicine, create_sale, daily_summary, search_medicines

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/login")
def api_login():
    body = request.get_json(silent=True) or {}
    user = authenticate(body.get("username", ""), body.get("password", ""), tenant_slug=body.get("tenant_slug"))
    if not user:
        return {"error": "Invalid credentials"}, 401
    token, expires_at = issue_api_token(user["id"], user["tenant_id"])
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_at": expires_at,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "tenant_id": user["tenant_id"],
            "tenant_slug": user["tenant_slug"],
        },
    }


@api_bp.post("/logout")
@api_auth_required
def api_logout():
    revoke_api_token(g.api_token)
    return {"status": "logged_out"}


@api_bp.get("/health")
def api_health():
    return {"status": "ok", "date": date.today().isoformat()}


@api_bp.get("/medicines")
@api_auth_required
def api_medicines_search():
    query = request.args.get("q", "")
    rows = search_medicines(query, tenant_id=g.api_user["tenant_id"]) if query else []
    return {
        "count": len(rows),
        "items": [dict(r) for r in rows],
    }


@api_bp.post("/medicines")
@api_auth_required
def api_add_medicine():
    body = request.get_json(silent=True) or {}
    try:
        med_id = add_medicine(body, tenant_id=g.api_user["tenant_id"])
        return {"id": med_id}, 201
    except (ValidationError, KeyError, ValueError) as exc:
        return {"error": str(exc)}, 400


@api_bp.post("/sales")
@api_auth_required
def api_create_sale():
    body = request.get_json(silent=True) or {}
    try:
        sale_id = create_sale(
            medicine_id=int(body["medicine_id"]),
            strips_sold=int(body.get("strips_sold", 0)),
            tablets_sold=int(body.get("tablets_sold", 0)),
            payment_mode=body["payment_mode"],
            customer_name=body.get("customer_name", ""),
            user_id=g.api_user["user_id"],
            tenant_id=g.api_user["tenant_id"],
        )
        return {"id": sale_id}, 201
    except (ValidationError, KeyError, ValueError) as exc:
        return {"error": str(exc)}, 400


@api_bp.get("/summary/daily")
@api_auth_required
def api_daily_summary():
    day = request.args.get("day")
    totals, sales = daily_summary(day, tenant_id=g.api_user["tenant_id"])
    return {
        "totals": dict(totals),
        "sales": [dict(s) for s in sales],
    }
