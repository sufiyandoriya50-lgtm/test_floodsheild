
import os

from app import create_app
from app.config import DevelopmentConfig, ProductionConfig


# Select the application configuration based on the environment.
environment = os.getenv("APP_ENV", "development").lower()

configurations = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

config_class = configurations.get(environment)

if config_class is None:
    raise ValueError(
        "Invalid APP_ENV. Use 'development' or 'production'."
    )

# Create the Flask application using the selected configuration.
app = create_app(config_class)


# Start the Flask development server using the selected debug setting.
if __name__ == "__main__":
    app.run(
        debug=app.config["DEBUG"],
        host="127.0.0.1",
        port=5000
    )
