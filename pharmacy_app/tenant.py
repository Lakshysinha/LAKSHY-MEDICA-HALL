from flask import g, request, session


def resolve_tenant_code() -> str:
    code = request.headers.get("X-Tenant-Code") or request.args.get("tenant") or session.get("tenant_code")
    return (code or "default").strip().lower()


def set_request_tenant(tenant_row) -> None:
    g.tenant = tenant_row
    session["tenant_id"] = tenant_row["id"]
    session["tenant_code"] = tenant_row["code"]


def get_tenant_id() -> int:
    tenant = g.get("tenant")
    if tenant:
        return tenant["id"]
    return int(session.get("tenant_id", 1))
