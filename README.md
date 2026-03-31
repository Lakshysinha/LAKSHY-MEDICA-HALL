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
- `SECRET_KEY`
- `DB_PATH`
- `SESSION_COOKIE_SECURE`
- `SESSION_TTL_SECONDS`
- `API_TOKEN_TTL_SECONDS`
- `DEFAULT_OWNER_USERNAME`
- `DEFAULT_OWNER_PASSWORD`
- `DEFAULT_TENANT_SLUG`
- `DEFAULT_TENANT_NAME`
- `LOG_LEVEL`

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
```bash
curl http://localhost:5000/api/summary/daily \
  -H 'Authorization: Bearer <TOKEN>'
```

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
```bash
python -m unittest discover -s tests -p 'test_*.py'
```
