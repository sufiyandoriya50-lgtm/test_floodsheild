import pytest

from datetime import datetime, timezone

from app import create_app
from app.config import TestingConfig
from app.extensions import db

from app.models.historical_flood_event import HistoricalFloodEvent

from app.services.historical_flood_query_service import (
    get_historical_flood_event,
    get_all_historical_flood_events
)


@pytest.fixture
def app():

    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        event1 = HistoricalFloodEvent(
            event_name="Ahmedabad Flood 2023",
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime(
                2023, 7, 22,
                tzinfo=timezone.utc
            ),
            severity="high",
            source="Official Dataset"
        )

        event2 = HistoricalFloodEvent(
            event_name="Ahmedabad Flood 2022",
            latitude=23.0300,
            longitude=72.5800,
            event_date=datetime(
                2022, 8, 15,
                tzinfo=timezone.utc
            ),
            severity="moderate",
            source="Official Dataset"
        )

        db.session.add_all([event1, event2])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


def test_get_event_by_id(app):

    with app.app_context():

        event = get_historical_flood_event(1)

        assert event is not None
        assert event.event_name == "Ahmedabad Flood 2023"


def test_get_nonexistent_event(app):

    with app.app_context():

        event = get_historical_flood_event(999)

        assert event is None


def test_filter_events_by_severity(app):

    with app.app_context():

        result = get_all_historical_flood_events(
            severity="high"
        )

        assert result.total == 1
        assert result.items[0].severity == "high"


def test_filter_events_by_location(app):

    with app.app_context():

        result = get_all_historical_flood_events(
            latitude=23.0225,
            longitude=72.5714,
            radius_km=5
        )

        assert result["total"] == 2


def test_location_filter_requires_all_parameters(app):

    with app.app_context():

        with pytest.raises(ValueError):

            get_all_historical_flood_events(
                latitude=23.0225,
                longitude=72.5714
            )


def test_pagination(app):

    with app.app_context():

        result = get_all_historical_flood_events(
            page=1,
            per_page=1
        )

        assert len(result.items) == 1
        assert result.total == 2

def test_filter_events_by_date_range(app):

    with app.app_context():

        result = get_all_historical_flood_events(
            start_date="2023-01-01",
            end_date="2023-12-31"
        )

        assert result.total == 1
        assert result.items[0].event_name == "Ahmedabad Flood 2023"


def test_invalid_severity_is_rejected(app):

    with app.app_context():

        with pytest.raises(ValueError):

            get_all_historical_flood_events(
                severity="extreme"
            )


def test_invalid_date_is_rejected(app):

    with app.app_context():

        with pytest.raises(ValueError):

            get_all_historical_flood_events(
                start_date="not-a-date"
            )


def test_start_date_after_end_date_is_rejected(app):

    with app.app_context():

        with pytest.raises(ValueError):

            get_all_historical_flood_events(
                start_date="2024-01-01",
                end_date="2023-01-01"
            )


def test_invalid_coordinates_are_rejected(app):

    with app.app_context():

        with pytest.raises(ValueError):

            get_all_historical_flood_events(
                latitude=200,
                longitude=72.5714,
                radius_km=5
            )
def test_end_date_includes_entire_day(app):

    with app.app_context():

        event = HistoricalFloodEvent(
            event_name="December 31 Flood",
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime(
                2023, 12, 31, 18, 30,
                tzinfo=timezone.utc
            ),
            severity="high",
            source="Official Dataset"
        )

        db.session.add(event)
        db.session.commit()

        result = get_all_historical_flood_events(
            start_date="2023-01-01",
            end_date="2023-12-31"
        )

        names = [item.event_name for item in result.items]

        assert "December 31 Flood" in names            