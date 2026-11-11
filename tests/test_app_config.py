
import pytest

from app import create_app
from app.config import (
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig
)


# Ensures production cannot start without Firebase credentials.
def test_production_requires_firebase_credentials(monkeypatch):

    from app import initialize_firebase
    # Configure a valid PostgreSQL URL for this production test.
    monkeypatch.setattr(
        ProductionConfig,
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://user:password@localhost/floodshield"
    )
    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        "redis://localhost:6379/0"
    )
    monkeypatch.setattr(

        ProductionConfig,
        "FIREBASE_CREDENTIALS_PATH",
        None
    )

    with pytest.raises(
        RuntimeError,
        match="FIREBASE_CREDENTIALS_PATH is required in production"
    ):
        create_app(ProductionConfig)


# Ensures production initializes Firebase when a credentials path is configured.
def test_production_initializes_firebase_when_configured(monkeypatch):

    from app import initialize_firebase as original_initialize_firebase
    import app as application

    initialized_paths = []

    def mock_initialize_firebase(credentials_path):
        initialized_paths.append(credentials_path)
        
    monkeypatch.setattr(
        ProductionConfig,
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://user:password@localhost/floodshield"
    )
    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        "redis://localhost:6379/0"
    )
    monkeypatch.setattr(
        ProductionConfig,
        "FIREBASE_CREDENTIALS_PATH",
        "test-service-account.json"
    )

    monkeypatch.setattr(
        application,
        "initialize_firebase",
        mock_initialize_firebase
    )

    create_app(ProductionConfig)

    assert initialized_paths == ["test-service-account.json"]


# Ensures automated tests do not require Firebase credentials.
def test_testing_configuration_skips_firebase(monkeypatch):

    import app as application

    def unexpected_firebase_initialization(credentials_path):
        pytest.fail("Firebase should not initialize during automated tests")

    monkeypatch.setattr(
        application,
        "initialize_firebase",
        unexpected_firebase_initialization
    )

    create_app(TestingConfig)


# Ensures local development can run without Firebase credentials.
def test_development_allows_missing_firebase_credentials(monkeypatch):

    import app as application

    initialized_paths = []

    def mock_initialize_firebase(credentials_path):
        initialized_paths.append(credentials_path)
        return None

    monkeypatch.setattr(
        DevelopmentConfig,
        "FIREBASE_CREDENTIALS_PATH",
        None
    )

    monkeypatch.setattr(
        application,
        "initialize_firebase",
        mock_initialize_firebase
    )

    create_app(DevelopmentConfig)

    assert initialized_paths == [None]

# Ensures production rejects a missing database URL.
def test_production_rejects_missing_database_url(monkeypatch):
    monkeypatch.setattr(
        ProductionConfig,
        "SQLALCHEMY_DATABASE_URI",
        None
    )

    with pytest.raises(
        RuntimeError,
        match="DATABASE_URL is required in production"
    ):
        ProductionConfig.validate_database_config()


# Ensures production rejects SQLite database URLs.
def test_production_rejects_sqlite_database(monkeypatch):
    monkeypatch.setattr(
        ProductionConfig,
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///floodshield.db"
    )

    with pytest.raises(
        RuntimeError,
        match="Production requires a PostgreSQL database"
    ):
        ProductionConfig.validate_database_config()


# Ensures production accepts a PostgreSQL database URL.
def test_production_accepts_postgresql_database(monkeypatch):
    monkeypatch.setattr(
        ProductionConfig,
        "SQLALCHEMY_DATABASE_URI",
        "postgresql://user:password@localhost/floodshield"
    )

    ProductionConfig.validate_database_config()
# Ensures production rejects missing rate-limit storage.
def test_production_rejects_missing_rate_limit_storage(monkeypatch):
    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        None
    )

    with pytest.raises(
        RuntimeError,
        match="RATELIMIT_STORAGE_URI is required in production"
    ):
        ProductionConfig.validate_rate_limit_config()


# Ensures production rejects in-memory rate-limit storage.
def test_production_rejects_memory_rate_limit_storage(monkeypatch):
    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )

    with pytest.raises(
        RuntimeError,
        match="Production requires shared rate-limit storage"
    ):
        ProductionConfig.validate_rate_limit_config()


# Ensures production accepts Redis rate-limit storage configuration.
def test_production_accepts_redis_rate_limit_storage(monkeypatch):
    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        "redis://localhost:6379/0"
    )

    ProductionConfig.validate_rate_limit_config()
