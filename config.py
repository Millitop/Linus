"""Application configuration.

Values are read from environment variables so the same codebase runs
identically on a developer machine and on the Raspberry Pi. See
.env.example for the full list of supported variables.
"""
import os
from datetime import timedelta


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(os.getcwd(), "instance", "gardskort.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Yard/site display name, shown in templates and on the kiosk screen.
    SITE_NAME = os.environ.get("SITE_NAME", "Fritidshemmet")

    # Card / token behaviour
    CARD_TOKEN_BYTES = int(os.environ.get("CARD_TOKEN_BYTES", "32"))
    RETRIEVAL_PIN_LENGTH = int(os.environ.get("RETRIEVAL_PIN_LENGTH", "6"))

    # Gate scan behaviour
    SCAN_DEBOUNCE_SECONDS = int(os.environ.get("SCAN_DEBOUNCE_SECONDS", "3"))

    # Nightly auto check-out, "HH:MM" 24h local time.
    AUTO_CHECKOUT_TIME = os.environ.get("AUTO_CHECKOUT_TIME", "18:00")

    # GDPR log retention, in days. 0 disables automatic purging.
    LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "365"))

    # Future extension point only -- no real cloud backend is implemented.
    SYNC_ENABLED = _bool_env("SYNC_ENABLED", False)

    # Rate limiting storage (Flask-Limiter). In-memory is fine for a
    # single-process kiosk deployment.
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    REMEMBER_COOKIE_DURATION = timedelta(hours=12)


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
