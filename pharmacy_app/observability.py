import logging
import time

from flask import Response, current_app, g, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter("lakshy_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("lakshy_http_request_latency_seconds", "HTTP request latency", ["method", "endpoint"])


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return (
            f'{{"level":"{record.levelname}","logger":"{record.name}","message":"{record.getMessage()}",'
            f'"time":"{self.formatTime(record, self.datefmt)}"}}'
        )


def init_observability(app):
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    app.logger.handlers = [handler]
    app.logger.setLevel(app.config["LOG_LEVEL"])

    @app.before_request
    def _start_timer():
        g.request_started_at = time.perf_counter()

    @app.after_request
    def _record_metrics(response):
        endpoint = request.endpoint or "unknown"
        duration = max(time.perf_counter() - g.get("request_started_at", time.perf_counter()), 0)
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
        current_app.logger.info(
            f"request method={request.method} path={request.path} status={response.status_code} duration_ms={duration * 1000:.2f}"
        )
        return response

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
