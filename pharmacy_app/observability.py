import json
import logging
import time
import uuid

from flask import Response, current_app, g, request

from .db import get_connection


def configure_logging(app):
    logging.basicConfig(level=getattr(logging, app.config["LOG_LEVEL"], logging.INFO))


def register_observability(app):
    configure_logging(app)

    @app.before_request
    def before_request_metrics():
        g.request_start = time.perf_counter()
        g.request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    @app.after_request
    def after_request_metrics(response):
        duration_ms = round((time.perf_counter() - g.get("request_start", time.perf_counter())) * 1000, 2)
        tenant = g.get("tenant")
        tenant_id = tenant["id"] if tenant else None
        try:
            conn = get_connection()
            conn.execute(
                """
                INSERT INTO request_logs (tenant_id, method, path, status_code, duration_ms, request_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (tenant_id, request.method, request.path, response.status_code, duration_ms, g.get("request_id")),
            )
            conn.commit()
        except Exception:
            app.logger.exception("Failed to persist request log")

        app.logger.info(
            json.dumps(
                {
                    "event": "request.complete",
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "tenant_id": tenant_id,
                    "request_id": g.get("request_id"),
                }
            )
        )
        response.headers["X-Request-Id"] = g.get("request_id", "")
        return response

    @app.get("/metrics")
    def metrics():
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT status_code, COUNT(*) AS total
            FROM request_logs
            WHERE created_at >= datetime('now', '-1 day')
            GROUP BY status_code
            ORDER BY status_code
            """
        ).fetchall()
        lines = [
            "# HELP app_requests_24h HTTP requests in the last 24 hours grouped by status.",
            "# TYPE app_requests_24h gauge",
        ]
        for row in rows:
            lines.append(f'app_requests_24h{{status="{row["status_code"]}"}} {row["total"]}')
        return Response("\n".join(lines) + "\n", mimetype="text/plain; version=0.0.4")
