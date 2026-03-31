import os
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parent.parent / "data" / "pharmacy.db"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
    API_TOKEN_TTL_SECONDS = int(os.getenv("API_TOKEN_TTL_SECONDS", "3600"))
    DEFAULT_OWNER_USERNAME = os.getenv("DEFAULT_OWNER_USERNAME", "owner")
    DEFAULT_OWNER_PASSWORD = os.getenv("DEFAULT_OWNER_PASSWORD", "owner123")
    DEFAULT_TENANT_SLUG = os.getenv("DEFAULT_TENANT_SLUG", "default")
    DEFAULT_TENANT_NAME = os.getenv("DEFAULT_TENANT_NAME", "Lakshy Medical Hall")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class TestConfig(Config):
    TESTING = True
    DB_PATH = Path("/tmp/lakshy_medical_test.db")
