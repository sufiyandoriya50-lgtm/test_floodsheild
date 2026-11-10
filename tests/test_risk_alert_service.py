
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.extensions import db
from app.models.user import User
from app.models.flood_report import FloodReport
from app.models.notification import Notification
from app.services.risk_alert_service import (
    send_nearby_risk_alerts,
    is_duplicate_alert
)


# Creates three citizen accounts for testing nearby and distant flood reports.
@pytest.fixture()
def citizens(app):
    with app.app_context():
        users = []

        for number in range(1, 4):
            user = User(
                name=f"Test Citizen {number}",
                email=f"risk_alert_test{number}@example.com"
            )
            user.set_password("TestPassword123")
            db.session.add(user)
            users.append(user)

        db.session.commit()

        user_ids = [user.id for user in users]

        yield {
            "nearby": user_ids[0],
            "pending": user_ids[1],
            "distant": user_ids[2]
        }


# Creates verified and pending reports around an assessed FloodShield location.
@pytest.fixture()
def community_reports(app, citizens):
    with app.app_context():
        reports = [
            FloodReport(
                user_id=citizens["nearby"],
                latitude=23.0230,
                longitude=72.5720,
                description="Verified nearby waterlogging report",
                status="verified"
            ),
            FloodReport(
                user_id=citizens["pending"],
                latitude=23.0235,
                longitude=72.5725,
                description="Pending nearby waterlogging report",
                status="pending"
            ),
            FloodReport(
                user_id=citizens["distant"],
                latitude=23.2000,
                longitude=72.8000,
                description="Verified distant waterlogging report",
                status="verified"
            )
        ]

        db.session.add_all(reports)
        db.session.commit()

        yield reports


# Tests that Low and Moderate risk assessments do not generate automatic alerts.
@pytest.mark.parametrize("risk_level", ["low", "moderate"])
def test_low_and_moderate_risk_do_not_trigger_alerts(app, risk_level):
    with app.app_context():
        result = send_nearby_risk_alerts(
            latitude=23.0225,
            longitude=72.5714,
            risk_level=risk_level
        )

        assert result["status"] == "skipped"
        assert result["notifications_created"] == 0
        assert result["duplicates_skipped"] == 0


# Tests that only users with verified reports inside the radius receive alerts.
def test_high_risk_alert_targets_verified_nearby_users(
    app,
    citizens,
    community_reports,
    monkeypatch
):
    with app.app_context():
        sent_notifications = []

        # Replaces Firebase notification delivery with a safe test function.
        def fake_send_notification(**kwargs):
            sent_notifications.append(kwargs)
            return SimpleNamespace(delivery_status="pending")

        monkeypatch.setattr(
            "app.services.risk_alert_service.send_notification",
            fake_send_notification
        )

        result = send_nearby_risk_alerts(
            latitude=23.0225,
            longitude=72.5714,
            risk_level="high",
            radius_km=3
        )

        assert result["eligible_users"] == 1
        assert result["notifications_created"] == 1
        assert result["duplicates_skipped"] == 0
        assert result["failed_users"] == []

        assert len(sent_notifications) == 1
        assert sent_notifications[0]["user_id"] == citizens["nearby"]
        assert sent_notifications[0]["risk_level"] == "high"


# Tests that Severe risk produces the correct alert title and severity.
def test_severe_risk_generates_severe_alert(
    app,
    citizens,
    community_reports,
    monkeypatch
):
    with app.app_context():
        sent_notifications = []

        def fake_send_notification(**kwargs):
            sent_notifications.append(kwargs)
            return SimpleNamespace(delivery_status="pending")

        monkeypatch.setattr(
            "app.services.risk_alert_service.send_notification",
            fake_send_notification
        )

        result = send_nearby_risk_alerts(
            latitude=23.0225,
            longitude=72.5714,
            risk_level="severe",
            radius_km=3
        )

        assert result["notifications_created"] == 1
        assert sent_notifications[0]["risk_level"] == "severe"
        assert sent_notifications[0]["title"] == "Severe Flood Risk Alert"


# Tests that an existing equal-severity alert suppresses a duplicate.
def test_recent_equal_severity_alert_is_duplicate(
    app,
    citizens
):
    with app.app_context():
        user_id = citizens["nearby"]
        deduplication_key = "flood_alert:1:23.023:72.571"

        previous_notification = Notification(
            user_id=user_id,
            title="High Flood Risk Alert",
            message="High flood risk detected.",
            notification_type="flood_alert",
            risk_level="high",
            deduplication_key=deduplication_key,
            delivery_status="sent",
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(previous_notification)
        db.session.commit()

        assert is_duplicate_alert(
            user_id,
            deduplication_key,
            "high"
        ) is True


# Tests that a more severe new alert is allowed to escalate an earlier alert.
def test_severe_alert_can_escalate_previous_high_alert(
    app,
    citizens
):
    with app.app_context():
        user_id = citizens["nearby"]
        deduplication_key = "flood_alert:1:23.023:72.571"

        previous_notification = Notification(
            user_id=user_id,
            title="High Flood Risk Alert",
            message="High flood risk detected.",
            notification_type="flood_alert",
            risk_level="high",
            deduplication_key=deduplication_key,
            delivery_status="sent",
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(previous_notification)
        db.session.commit()

        assert is_duplicate_alert(
            user_id,
            deduplication_key,
            "severe"
        ) is False


# Tests that a user who disables push notifications is excluded from alerts.
def test_push_disabled_user_does_not_receive_alert(
    app,
    citizens,
    community_reports,
    monkeypatch
):
    with app.app_context():
        monkeypatch.setattr(
            "app.services.risk_alert_service.get_or_create_preferences",
            lambda user_id: SimpleNamespace(
                push_enabled=False,
                high_risk_enabled=True,
                severe_risk_enabled=True
            )
        )

        sent_notifications = []

        monkeypatch.setattr(
            "app.services.risk_alert_service.send_notification",
            lambda **kwargs: sent_notifications.append(kwargs)
        )

        result = send_nearby_risk_alerts(
            latitude=23.0225,
            longitude=72.5714,
            risk_level="high",
            radius_km=3
        )

        assert result["eligible_users"] == 1
        assert result["notifications_created"] == 0
        assert sent_notifications == []


# Tests that disabling High-risk alerts does not disable Severe-risk alerts.
def test_high_risk_preference_does_not_block_severe_alerts(
    app,
    citizens,
    community_reports,
    monkeypatch
):
    with app.app_context():
        monkeypatch.setattr(
            "app.services.risk_alert_service.get_or_create_preferences",
            lambda user_id: SimpleNamespace(
                push_enabled=True,
                high_risk_enabled=False,
                severe_risk_enabled=True
            )
        )

        sent_notifications = []

        monkeypatch.setattr(
            "app.services.risk_alert_service.send_notification",
            lambda **kwargs: sent_notifications.append(kwargs)
        )

        result = send_nearby_risk_alerts(
            latitude=23.0225,
            longitude=72.5714,
            risk_level="severe",
            radius_km=3
        )

        assert result["notifications_created"] == 1
        assert sent_notifications[0]["risk_level"] == "severe"


# Tests that a notification delivery exception is recorded for the affected user.
def test_failed_notification_delivery_is_reported(
    app,
    citizens,
    community_reports,
    monkeypatch
):
    with app.app_context():
        def fail_notification(**kwargs):
            raise RuntimeError("Simulated notification failure")

        monkeypatch.setattr(
            "app.services.risk_alert_service.send_notification",
            fail_notification
        )

        result = send_nearby_risk_alerts(
            latitude=23.0225,
            longitude=72.5714,
            risk_level="high",
            radius_km=3
        )

        assert result["notifications_created"] == 0
        assert result["failed_users"] == [citizens["nearby"]]
