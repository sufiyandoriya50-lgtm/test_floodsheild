
from flask import Flask
from app.extensions import db, migrate, jwt


#to Make models of db discoverable to Flask-Migrate
from app import models
from app.models.moderation_history import ModerationHistory

#importing the api's from routes by blueprint
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
def create_app(config_class=None):
    """
    Application factory for the FloodShield backend.

    Creates and configures the Flask application.
    """

    # Create Flask application
    app = Flask(__name__)

    # Load application configuration
    if config_class is None:
        from app.config import DevelopmentConfig
        config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # Initialize Flask extensions
    # Initialize Firebase when the application is not running automated tests.
    if not app.config.get("TESTING"):
        initialize_firebase(
            app.config.get("FIREBASE_CREDENTIALS_PATH")
        )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register API routes here in future steps

    # Register API blueprints (regitration connects api routes to main flask app  )
    app.register_blueprint(health_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(historical_floods_bp)
    app.register_blueprint(historical_weather_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(notifications_bp)

    #default home page api to get respose on direct url 
    @app.route("/", methods=["GET"])
    def home():
        return {
            "application": "FloodShield",
            "message": "FloodShield Backend API is running",
            "status": "success"
        }, 200

    return app
