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
    #photo upload max total size to 16 max with 3 pics
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Weather API
    WEATHER_API_URL = os.getenv(
        "WEATHER_API_URL",
        "https://api.open-meteo.com/v1/forecast"
    )
    #firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
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


class ProductionConfig(Config):
    """Configuration for production deployment."""

    DEBUG = False