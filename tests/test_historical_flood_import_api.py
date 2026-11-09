import io

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.user import User
from app.models.historical_flood_event import HistoricalFloodEvent


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_tokens(app):
    with app.app_context():
        admin = User(
            name="Import Administrator",
            email="import_admin@example.com",
            role="admin",
        )

        citizen = User(
            name="Import Citizen",
            email="import_citizen@example.com",
            role="citizen",
        )

        admin.set_password("AdminPassword123")
        citizen.set_password("CitizenPassword123")

        db.session.add_all([admin, citizen])
        db.session.commit()

        return {
            "admin": create_access_token(identity=str(admin.id)),
            "citizen": create_access_token(identity=str(citizen.id)),
        }


def test_import_csv_requires_authentication(client):
    response = client.post(
        "/api/admin/historical-floods/import"
    )

    assert response.status_code == 401


def test_citizen_cannot_import_csv(client, user_tokens):
    response = client.post(
        "/api/admin/historical-floods/import",
        headers={
            "Authorization": f"Bearer {user_tokens['citizen']}"
        },
    )

    assert response.status_code == 403


def test_admin_can_import_csv(client, app, user_tokens):
    csv_content = (
        "event_name,latitude,longitude,event_date,"
        "water_depth_cm,severity,description,source\n"
        "Ahmedabad Flood Test,23.0225,72.5714,"
        "2023-07-20T10:30:00+00:00,45,high,"
        "Heavy waterlogging,Test Dataset\n"
    )

    response = client.post(
        "/api/admin/historical-floods/import",
        data={
            "file": (
                io.BytesIO(csv_content.encode("utf-8")),
                "historical_floods.csv",
            )
        },
        headers={
            "Authorization": f"Bearer {user_tokens['admin']}"
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.json["result"]["imported_count"] == 1
    assert response.json["result"]["failed_count"] == 0

    with app.app_context():
        assert HistoricalFloodEvent.query.count() == 1


def test_import_rejects_non_csv_file(client, user_tokens):
    response = client.post(
        "/api/admin/historical-floods/import",
        data={
            "file": (
                io.BytesIO(b"This is not a CSV"),
                "document.txt",
            )
        },
        headers={
            "Authorization": f"Bearer {user_tokens['admin']}"
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400