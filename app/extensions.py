
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager


# Database extension
db = SQLAlchemy()

# Database migration extension
migrate = Migrate()

# JWT authentication extension
jwt = JWTManager()
