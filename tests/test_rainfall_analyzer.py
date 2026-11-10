
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

from app.risk.rainfall_analyzer import analyze_rainfall


def test_analyze_high_rainfall():
    now = datetime.now(timezone.utc)

    record = SimpleNamespace(
        rainfall_mm=5.0,
        precipitation_interval_seconds=900,
        recorded_at=now,
    )

    result = analyze_rainfall([record], now=now)

    assert result["available"] is True
    assert result["score"] == 80
    assert result["category"] == "severe"
    assert result["maximum_rainfall_rate_mm_per_hour"] == 20.0


def test_unknown_interval_is_not_treated_as_zero_rainfall():
    now = datetime.now(timezone.utc)

    record = SimpleNamespace(
        rainfall_mm=5.0,
        precipitation_interval_seconds=None,
        recorded_at=now,
    )

    result = analyze_rainfall([record], now=now)

    assert result["available"] is False
    assert result["score"] is None
    assert result["category"] == "insufficient_data"


def test_old_weather_observation_is_rejected():
    now = datetime.now(timezone.utc)

    record = SimpleNamespace(
        rainfall_mm=5.0,
        precipitation_interval_seconds=900,
        recorded_at=now - timedelta(hours=5),
    )

    result = analyze_rainfall([record], now=now)

    assert result["available"] is False
    assert result["score"] is None


def test_no_weather_records():
    result = analyze_rainfall([])

    assert result["available"] is False
    assert result["category"] == "insufficient_data"
