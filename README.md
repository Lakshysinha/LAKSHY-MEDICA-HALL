# Lakshy Medical Hall

Production-oriented pharmacy management platform with Web UI + API, now hardened with TLS reverse proxy patterns, metrics, migration automation, and tenant isolation.

## Implemented features
- Medicine master, inventory, sales, short-list, and daily summary.
- Session auth for web and bearer auth for API.
- Tenant-aware data isolation (users, medicines, sales, tokens).
- Automated DB migrations at startup using `schema_migrations`.
- `/health`, `/api/health`, and `/metrics` endpoints.
- Structured JSON application logging for centralized ingestion.
- Docker Compose stack with app + Nginx reverse proxy + Prometheus.

## Configuration
Copy `.env.example` to `.env` and set values:
Production-oriented pharmacy management platform with both Web UI and API interfaces.

## What is implemented now

- **Medicine master**: full metadata, batch, MFG/EXP, stock, pricing, code/scanner value.
- **Inventory controls**: validation for stock and dates, auto low-stock Short List (`<=3`).
- **Sales entry**: strips/tablets, customer name (optional), payment mode (`cash`/`online`).
- **Daily reporting**: medicines sold, total sales, cash total, online total.
- **Authentication**:
  - Session auth for web UI.
  - Token auth for API (`/api/login`, `/api/logout`) with DB-stored token revocation and expiry.
- **Advanced hardening**:
  - Tenant isolation via `tenants` and `tenant_id` scoped data access.
  - Reverse proxy + TLS via Nginx.
  - Centralized request log capture and `/metrics` endpoint.
  - Automated migration runner.

## Repository layout

- `pharmacy_app/` - app package (web routes + API + service layer + DB + auth + observability)
- `deploy/nginx/` - production reverse proxy configuration
- `docs/` - phase-wise delivery and deployment guides
- `scripts/` - operational scripts (backup / restore / migrate)
- **Operational controls**:
  - Config via environment variables.
  - Health endpoints (`/health`, `/api/health`).
  - Backup/restore script for SQLite data.
  - Dockerized runtime and Gunicorn app server.

## Repository layout

- `pharmacy_app/` - app package (web routes + API + service layer + DB + auth)
- `docs/` - phase-wise delivery and deployment guides
- `scripts/` - operational scripts (backup / restore)
- `tests/` - tests
- `run.py` - local development entrypoint
- `wsgi.py` - production WSGI entrypoint

## Configuration

Copy `.env.example` to `.env` and update:

- `SECRET_KEY`
- `DB_PATH`
- `SESSION_COOKIE_SECURE`
- `SESSION_TTL_SECONDS`
- `API_TOKEN_TTL_SECONDS`
- `DEFAULT_OWNER_USERNAME`
- `DEFAULT_OWNER_PASSWORD`
- `DEFAULT_TENANT_CODE`
- `DEFAULT_TENANT_SLUG`
- `DEFAULT_TENANT_NAME`
- `LOG_LEVEL`

## Local run

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## API quick start
```bash
curl -X POST http://localhost:5000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"owner","password":"owner123","tenant_slug":"default"}'
```

Use token:
Default owner credentials come from env vars:
- `DEFAULT_OWNER_USERNAME`
- `DEFAULT_OWNER_PASSWORD`

## API quick start

1. Login and get token:
```bash
curl -X POST http://localhost:5000/api/login \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Code: default' \
  -d '{"username":"owner","password":"owner123"}'
```
2. Use token:
```bash
curl http://localhost:5000/api/summary/daily \
  -H 'Authorization: Bearer <TOKEN>'
```

## Production deployment (Docker + Nginx TLS)

```bash
cp .env.example .env
mkdir -p deploy/certs
# place fullchain.pem and privkey.pem into deploy/certs/
docker compose up --build -d
```

## Run migrations

```bash
python scripts/migrate.py
## Production deployment
1. Put TLS cert files at:
   - `deploy/certs/tls.crt`
   - `deploy/certs/tls.key`
2. Start stack:
```bash
docker compose up --build -d
```
3. Access:
- App through Nginx TLS: `https://localhost`
- Prometheus UI: `http://localhost:9090`

## Test command
## Production deployment (Docker)

```bash
docker compose up --build -d
```

## Test command

```bash
python -m unittest discover -s tests -p 'test_*.py'
```
