# Phase 6 - Production Grade Rollout

## Delivered hardening and rollout items

- Reverse proxy pattern with TLS termination via Nginx (`deploy/nginx/conf.d/pharmacy.conf`, `docker-compose.yml`).
- Centralized observability baseline:
  - JSON request logs from Flask app.
  - Prometheus-compatible app metrics at `/metrics`.
  - Prometheus service in Compose for metrics scraping.
- Multi-tenant isolation:
  - Added `tenants` table and tenant-scoped access for users, medicines, sales, and API tokens.
  - Tenant-aware web session and API auth flows.
- Automated DB migration framework:
  - `schema_migrations` tracking table.
  - Ordered startup migrations run automatically from app initialization.

## Operational notes

- Place real certs at `deploy/certs/tls.crt` and `deploy/certs/tls.key` before enabling HTTPS in production.
- Keep `SESSION_COOKIE_SECURE=true` in production.
- Collect app logs from container stdout into your log platform (ELK/Loki/Cloud logging).
- Config-driven app setup (`pharmacy_app/config.py`) with env-based secrets and TTL controls.
- API token lifecycle (`api_tokens` table) with expiry + revocation.
- Role-based authorization helper for web UI flows.
- Health endpoints for uptime checks (`/health`, `/api/health`).
- WSGI and Gunicorn production entrypoint (`wsgi.py`, `Dockerfile`).
- Container deployment config (`docker-compose.yml`).
- Backup/restore operational script (`scripts/backup_restore.py`).

## Remaining enterprise-level enhancements

- Add reverse proxy (Nginx) + TLS termination.
- Add centralized logs and metrics pipeline.
- Add multi-tenant data isolation if needed.
- Add automated DB migration framework.
