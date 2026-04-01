"""Run DB migrations for LAKSHY MEDICA HALL."""

from pharmacy_app import create_app
from pharmacy_app.migrations import run_migrations


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_migrations()
    print("Migrations applied successfully")
