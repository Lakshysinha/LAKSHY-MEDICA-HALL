# Phase 6 - Production Grade Rollout

## Delivered hardening and rollout items

- Config-driven app setup (`pharmacy_app/config.py`) with env-based secrets and TTL controls.
- API token lifecycle (`api_tokens` table) with expiry + revocation.
- Role-based authorization helper for web UI flows.
- Health endpoints for uptime checks (`/health`, `/api/health`).
- WSGI and Gunicorn production entrypoint (`wsgi.py`, `Dockerfile`).
- Container deployment config (`docker-compose.yml`).
- Backup/restore operational script (`scripts/backup_restore.py`).
- Reverse proxy and TLS termination with Nginx (`deploy/nginx/nginx.conf` + compose wiring).
- Centralized request logs (`request_logs` table + JSON logs) and `/metrics` endpoint.
- Tenant isolation model (`tenants` table + `tenant_id` scoping in auth/service flows).
- Automated DB migrations runner (`pharmacy_app/migrations.py`, `scripts/migrate.py`).

## Production checklist

- Mount valid TLS certificates under `deploy/certs/fullchain.pem` and `deploy/certs/privkey.pem`.
- Configure per-tenant client headers (`X-Tenant-Code`) for API consumers.
- Run `python scripts/migrate.py` as part of deployment pipeline before app restarts.
- Export application logs from container runtime to your centralized platform (ELK/OpenSearch/Cloud logging).
