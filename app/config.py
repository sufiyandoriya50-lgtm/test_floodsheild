import os
from dotenv import load_dotenv

# Load environment variables from the backend .env file
load_dotenv()


class Config:
    """Base configuration for FloodShield."""

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///floodshield.db"
    )
    # Maximum total HTTP request size, including multipart upload overhead.(17mb with total 3 pics is max )
    MAX_CONTENT_LENGTH = 17 * 1024 * 1024

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Application logging level.
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    # API rate limiting
    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )
    RATELIMIT_HEADERS_ENABLED = True
    # Weather API
    WEATHER_API_URL = os.getenv(
        "WEATHER_API_URL",
        "https://api.open-meteo.com/v1/forecast"
    )
    #firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
    # Whether Firebase credentials are mandatory in this environment.
    REQUIRE_FIREBASE = False
    # Application settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class DevelopmentConfig(Config):
    """Configuration for local development."""

    DEBUG = True


# Configuration used only during automated tests.
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "floodshield-testing-secret-key-2026-secure"
    SECRET_KEY = "floodshield-testing-secret-key-2026"


class ProductionConfig(Config):
    """Configuration for production deployment."""

    REQUIRE_FIREBASE = True
    DEBUG = False
    TESTING = False

    # Require an explicitly configured PostgreSQL database in production.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    # Production must use shared rate-limit storage.
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI")
    @classmethod
    def validate_database_config(cls):
        """Ensure production uses a valid PostgreSQL connection URL."""

        database_url = cls.SQLALCHEMY_DATABASE_URI

        if not database_url:
            raise RuntimeError(
                "DATABASE_URL is required in production."
            )

        if not database_url.startswith(
            ("postgresql://", "postgresql+psycopg://")
        ):
            raise RuntimeError(
                "Production requires a PostgreSQL database."
            )
    @classmethod
    def validate_rate_limit_config(cls):
        """Ensure production uses shared rate-limit storage."""

        storage_uri = cls.RATELIMIT_STORAGE_URI

        if not storage_uri:
            raise RuntimeError(
                "RATELIMIT_STORAGE_URI is required in production."
            )

        if storage_uri.strip().lower().startswith("memory://"):
            raise RuntimeError(
                "Production requires shared rate-limit storage, not memory://."
            )    