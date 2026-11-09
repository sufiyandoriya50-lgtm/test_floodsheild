import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db


# Creates an isolated Flask application and database for every test.
@pytest.fixture()
def app(tmp_path):
    app = create_app(TestingConfig)

    # Store test photographs in a temporary folder, not the real upload folder.
    app.config["TEST_UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    app.instance_path = str(tmp_path / "instance")

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


# Provides a Flask test client for making API requests without starting a server.
@pytest.fixture()
def client(app):
    return app.test_client()

# Provides an authenticated test client with a valid JWT access token.
@pytest.fixture()
def auth_client(app, client):
    from flask_jwt_extended import create_access_token

    with app.app_context():
        access_token = create_access_token(identity="1")

    client.environ_base["HTTP_AUTHORIZATION"] = (
        f"Bearer {access_token}"
    )

    return client