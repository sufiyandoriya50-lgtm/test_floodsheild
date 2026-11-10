import pytest

from datetime import datetime, timezone

from app.services.historical_flood_service import (
    validate_historical_flood_event
)


def test_valid_historical_event():
    result = validate_historical_flood_event(
        latitude=23.0225,
        longitude=72.5714,
        event_date=datetime(
            2023, 7, 22, 10, 30,
            tzinfo=timezone.utc
        ),
        source="Official Historical Dataset",
        severity="high",
        water_depth_cm=40
    )

    assert result["latitude"] == 23.0225
    assert result["longitude"] == 72.5714
    assert result["severity"] == "high"
    assert result["water_depth_cm"] == 40


def test_invalid_latitude():
    with pytest.raises(ValueError):
        validate_historical_flood_event(
            latitude=150,
            longitude=72.5714,
            event_date=datetime.now(timezone.utc),
            source="Official Dataset"
        )


def test_invalid_longitude():
    with pytest.raises(ValueError):
        validate_historical_flood_event(
            latitude=23.0225,
            longitude=250,
            event_date=datetime.now(timezone.utc),
            source="Official Dataset"
        )


def test_negative_water_depth():
    with pytest.raises(ValueError):
        validate_historical_flood_event(
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime.now(timezone.utc),
            source="Official Dataset",
            water_depth_cm=-10
        )


def test_invalid_severity():
    with pytest.raises(ValueError):
        validate_historical_flood_event(
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime.now(timezone.utc),
            source="Official Dataset",
            severity="extreme"
        )


def test_missing_source():
    with pytest.raises(ValueError):
        validate_historical_flood_event(
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime.now(timezone.utc),
            source=" "
        )


def test_timezone_required():
    with pytest.raises(ValueError):
        validate_historical_flood_event(
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime(2023, 7, 22),
            source="Official Dataset"
        )