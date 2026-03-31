from flask import Flask

from .api import api_bp
from .auth import ensure_default_owner
from .config import Config
from .db import close_db, init_db
from .observability import init_observability
from .routes import register_routes


def create_app(test_config: dict | None = None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    with app.app_context():
        init_db()
        ensure_default_owner()

    init_observability(app)
    register_routes(app)
    app.register_blueprint(api_bp)
    app.teardown_appcontext(close_db)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app
