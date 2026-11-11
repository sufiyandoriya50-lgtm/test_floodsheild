import pytest

from datetime import datetime, timezone

from app import create_app
from app.config import TestingConfig
from app.extensions import db

from app.models.historical_flood_event import HistoricalFloodEvent
from sqlalchemy.exc import IntegrityError

from app.services.historical_flood_storage_service import (
    create_historical_flood_event
)


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_create_historical_flood_event(app):

    with app.app_context():

        event = create_historical_flood_event(
            event_name="Ahmedabad Historical Flood",
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime(
                2023, 7, 22, 10, 30,
                tzinfo=timezone.utc
            ),
            water_depth_cm=40,
            severity="high",
            description="Historical waterlogging event in Ahmedabad",
            source="Official Historical Dataset",
            source_reference="AHMEDABAD-FLOOD-2023"
        )

        saved_event = db.session.get(
            HistoricalFloodEvent,
            event.id
        )

        assert saved_event is not None
        assert saved_event.event_name == "Ahmedabad Historical Flood"
        assert saved_event.latitude == 23.0225
        assert saved_event.water_depth_cm == 40
        assert saved_event.severity == "high"
        assert saved_event.source == "Official Historical Dataset"


def test_invalid_event_is_not_saved(app):

    with app.app_context():

        with pytest.raises(ValueError):

            create_historical_flood_event(
                event_name="Invalid Flood",
                latitude=200,
                longitude=72.5714,
                event_date=datetime.now(timezone.utc),
                source="Official Dataset"
            )

        assert HistoricalFloodEvent.query.count() == 0

# Verify that the database rejects invalid historical flood event data.
@pytest.mark.parametrize(
    "invalid_fields",
    [
        {"latitude": 91},
        {"latitude": -91},
        {"longitude": 181},
        {"longitude": -181},
        {"water_depth_cm": -1},
        {"severity": "critical"},
        {"severity": "invalid"},
        {"source": ""},
        {"source": "   "},
        {"source": "S" * 101},
        {"event_name": ""},
        {"event_name": "   "},
        {"event_name": "E" * 151},
        {"source_reference": ""},
        {"source_reference": "   "},
        {"source_reference": "R" * 501},
    ]
)
def test_historical_flood_database_rejects_invalid_data(
    app,
    invalid_fields
):
    with app.app_context():
        event_data = {
            "event_name": "Test Historical Flood",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "event_date": datetime.now(timezone.utc),
            "water_depth_cm": 40,
            "severity": "high",
            "description": "Database integrity test",
            "source": "Official Dataset",
            "source_reference": "TEST-REFERENCE"
        }

        event_data.update(invalid_fields)

        event = HistoricalFloodEvent(**event_data)
        db.session.add(event)

        with pytest.raises(IntegrityError):
            db.session.flush()

        db.session.rollback()


# Verify that valid optional historical flood fields can remain NULL.
def test_historical_flood_database_accepts_optional_null_fields(app):
    with app.app_context():
        event = HistoricalFloodEvent(
            event_name=None,
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime.now(timezone.utc),
            water_depth_cm=None,
            severity=None,
            description=None,
            source="Official Dataset",
            source_reference=None
        )

        db.session.add(event)
        db.session.commit()

        saved_event = db.session.get(
            HistoricalFloodEvent,
            event.id
        )

        assert saved_event is not None
        assert saved_event.event_name is None
        assert saved_event.water_depth_cm is None
        assert saved_event.severity is None
        assert saved_event.source_reference is None
