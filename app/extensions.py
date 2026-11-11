
from sqlalchemy import event
from sqlalchemy.engine import Engine

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Enable foreign-key enforcement for every SQLite connection.
@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Enable SQLite foreign-key enforcement when opening a connection."""

    # Apply this setting only to SQLite connections.
    if dbapi_connection.__class__.__module__ == "sqlite3":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Database extension
db = SQLAlchemy()

# Database migration extension
migrate = Migrate()

# JWT authentication extension
jwt = JWTManager()

# API rate-limiting extension.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)