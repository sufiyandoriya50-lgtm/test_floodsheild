
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest

from app.risk.community_report_analyzer import (
    analyze_community_reports,
)


def make_report(
    status="verified",
    depth=50,
    age_days=0,
    latitude=23.0225,
    longitude=72.5714,
):
    return SimpleNamespace(
        status=status,
        water_depth_cm=depth,
        created_at=datetime.now(timezone.utc)
        - timedelta(days=age_days),
        latitude=latitude,
        longitude=longitude,
    )


def test_nearby_verified_report():
    now = datetime.now(timezone.utc)

    report = make_report(depth=50)

    result = analyze_community_reports(
        [report],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is True
    assert result["score"] == 75
    assert result["category"] == "severe"
    assert result["nearby_verified_reports"] == 1


def test_pending_report_is_ignored():
    now = datetime.now(timezone.utc)

    report = make_report(status="pending")

    result = analyze_community_reports(
        [report],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is False
    assert result["score"] is None


def test_old_report_is_ignored():
    now = datetime.now(timezone.utc)

    report = make_report(age_days=10)

    result = analyze_community_reports(
        [report],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is False


def test_report_outside_radius_is_ignored():
    now = datetime.now(timezone.utc)

    report = make_report(
        latitude=23.2,
        longitude=72.8,
    )

    result = analyze_community_reports(
        [report],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is False


def test_invalid_coordinates_are_rejected():
    with pytest.raises(ValueError):
        analyze_community_reports(
            [],
            latitude=100,
            longitude=72.5714,
        )


def test_unknown_water_depth():
    now = datetime.now(timezone.utc)

    report = make_report(depth=None)

    result = analyze_community_reports(
        [report],
        latitude=23.0225,
        longitude=72.5714,
        now=now,
    )

    assert result["available"] is True
    assert result["score"] == 50

