from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.risk.historical_weather_analyzer import analyze_historical_weather


"""Creates a sample historical weather record for testing."""

def make_weather_record(
    rainfall=5.0,
    interval=900,
    latitude=23.0225,
    longitude=72.5714,
    recorded_at=None,
):
    if recorded_at is None:
        recorded_at = datetime.now(timezone.utc)

    return SimpleNamespace(
        rainfall_mm=rainfall,
        precipitation_interval_seconds=interval,
        latitude=latitude,
        longitude=longitude,
        recorded_at=recorded_at,
    )


def test_analyze_recent_nearby_rainfall():
    now = datetime.now(timezone.utc)

    record = make_weather_record(
        rainfall=5.0,
        interval=900,
        recorded_at=now,
    )

    result = analyze_historical_weather(
        records=[record],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is True
    assert result["maximum_precipitation_rate_mm_per_hour"] == 20.0
    assert result["category"] == "severe"


def test_ignore_weather_outside_radius():
    now = datetime.now(timezone.utc)

    record = make_weather_record(
        latitude=23.2,
        longitude=72.5714,
        recorded_at=now,
    )

    result = analyze_historical_weather(
        records=[record],
        latitude=23.0225,
        longitude=72.5714,
        radius_km=5,
        now=now,
    )

    assert result["available"] is False


def test_ignore_weather_older_than_30_days():
    now = datetime.now(timezone.utc)

    record = make_weather_record(
        recorded_at=now - timedelta(days=31),
    )

    result = analyze_historical_weather(
        records=[record],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is False


def test_ignore_record_without_precipitation_interval():
    now = datetime.now(timezone.utc)

    record = make_weather_record(
        interval=None,
        recorded_at=now,
    )

    result = analyze_historical_weather(
        records=[record],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is False


def test_ignore_future_weather_record():
    now = datetime.now(timezone.utc)

    record = make_weather_record(
        recorded_at=now + timedelta(hours=1),
    )

    result = analyze_historical_weather(
        records=[record],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is False


def test_no_historical_weather_records():
    now = datetime.now(timezone.utc)

    result = analyze_historical_weather(
        records=[],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is False