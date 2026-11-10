
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest

from app.risk.historical_flood_analyzer import (
    analyze_historical_flood_risk,
)


def test_nearby_severe_flood_event():
    event = SimpleNamespace(
        latitude=23.0225,
        longitude=72.5714,
        severity="severe",
        event_date=datetime.now(timezone.utc) - timedelta(days=10),
    )

    result = analyze_historical_flood_risk(
        [event],
        latitude=23.0225,
        longitude=72.5714,
    )

    assert result["available"] is True
    assert result["score"] == 100
    assert result["category"] == "severe"
    assert result["nearby_events"] == 1


def test_event_outside_search_radius():
    event = SimpleNamespace(
        latitude=23.2,
        longitude=72.8,
        severity="severe",
        event_date=datetime.now(timezone.utc),
    )

    result = analyze_historical_flood_risk(
        [event],
        latitude=23.0225,
        longitude=72.5714,
    )

    assert result["available"] is False
    assert result["score"] is None


def test_no_historical_events():
    result = analyze_historical_flood_risk(
        [],
        latitude=23.0225,
        longitude=72.5714,
    )

    assert result["available"] is False
    assert result["category"] == "insufficient_data"


def test_invalid_latitude():
    with pytest.raises(ValueError):
        analyze_historical_flood_risk(
            [],
            latitude=100,
            longitude=72.5714,
        )


def test_future_event_is_ignored():
    event = SimpleNamespace(
        latitude=23.0225,
        longitude=72.5714,
        severity="severe",
        event_date=datetime.now(timezone.utc) + timedelta(days=10),
    )

    result = analyze_historical_flood_risk(
        [event],
        latitude=23.0225,
        longitude=72.5714,
    )

    assert result["available"] is False
    assert result["score"] is None
