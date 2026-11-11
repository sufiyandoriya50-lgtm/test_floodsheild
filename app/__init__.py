import logging
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from app.extensions import db, migrate, jwt, limiter

# Make database models discoverable to Flask-Migrate.
from app import models
from app.models.moderation_history import ModerationHistory

# Import API blueprints.
from app.routes.health import health_bp
from app.routes.weather import weather_bp
from app.routes.reports import reports_bp
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.risk import risk_bp
from app.routes.historical_floods import historical_floods_bp
from app.routes.historical_weather import historical_weather_bp
from app.routes.notifications import notifications_bp

from app.services.firebase_service import initialize_firebase


# Validates that required security configuration is available.
def validate_security_config(app):
    """Validate essential application security settings."""

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is missing from application configuration.")

    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT_SECRET_KEY is missing from application configuration.")

# Configures structured application logging.
def configure_logging(app):
    """Configure consistent application logging."""

    log_level = getattr(
        logging,
        app.config.get("LOG_LEVEL", "INFO"),
        logging.INFO
    )

    app.logger.setLevel(log_level)

    # Use an existing Flask handler or create one if necessary.
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        app.logger.addHandler(handler)

    # Apply a consistent timestamped format.
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s "
        "%(name)s: %(message)s"
    )

    for handler in app.logger.handlers:
        handler.setFormatter(formatter)

    # Avoid duplicate messages through the root logger.
    app.logger.propagate = False


# Registers consistent JSON error handlers for the application.
def register_error_handlers(app):
    """Return consistent JSON responses for HTTP and unexpected errors."""

    # Handle HTTP errors such as 404, 405 and 413.
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = {
            "status": "error",
            "error": error.name,
            "message": error.description
        }

        return jsonify(response), error.code

    # Handle unexpected internal server errors.
    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.exception(
            "Unhandled application exception"
        )

        return jsonify({
            "status": "error",
            "error": "Internal Server Error",
            "message": "An unexpected server error occurred."
        }), 500

# Creates and configures the Flask application.
def create_app(config_class=None):
    """Application factory for the FloodShield backend."""

    app = Flask(__name__)

    # Select the default configuration.
    if config_class is None:
        from app.config import DevelopmentConfig
        config_class = DevelopmentConfig
    app.config.from_object(config_class)
    # Configure application logging.
    configure_logging(app)
    # Validate essential application security settings.
    validate_security_config(app)
    
        # Validate production database and rate-limit storage configuration.
    if config_class.__name__ == "ProductionConfig":
        config_class.validate_database_config()
        config_class.validate_rate_limit_config()
        
    # Initialize Firebase outside automated tests.
    if not app.config.get("TESTING"):
        firebase_credentials_path = app.config.get(
            "FIREBASE_CREDENTIALS_PATH"
        )
    
        # Production must have Firebase credentials configured.
        if (
            app.config.get("REQUIRE_FIREBASE")
            and not firebase_credentials_path
        ):
            raise RuntimeError(
                "FIREBASE_CREDENTIALS_PATH is required in production."
            )
    
        # Initialize Firebase when credentials are configured.
        initialize_firebase(firebase_credentials_path)
    # Initialize Flask extensions.
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # Register API blueprints.
    app.register_blueprint(health_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(historical_floods_bp)
    app.register_blueprint(historical_weather_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(notifications_bp)

    # Register centralized JSON error handlers.
    register_error_handlers(app)

    # Default API endpoint.
    @app.route("/", methods=["GET"])
    def home():
        return {
            "application": "FloodShield",
            "message": "FloodShield Backend API is running",
            "status": "success"
        }, 200

    return app
