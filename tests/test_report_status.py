import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.user import User
from app.models.flood_report import FloodReport
from app.models.moderation_history import ModerationHistory
from app.services.report_service import update_report_status


def create_test_users():
    citizen = User(
        name="Test Citizen",
        email="status_test@example.com"
    )
    citizen.set_password("TestPassword123")

    admin = User(
        name="Test Admin",
        email="status_admin@example.com",
        role="admin"
    )
    admin.set_password("AdminPassword123")

    db.session.add_all([citizen, admin])
    db.session.commit()

    return citizen, admin


# Tests that a report can be verified and its moderation history is saved.
def test_update_report_status():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        try:
            citizen, admin = create_test_users()

            report = FloodReport(
                user_id=citizen.id,
                latitude=23.0225,
                longitude=72.5714,
                water_depth_cm=20,
                description="Waterlogging near Ahmedabad road"
            )

            db.session.add(report)
            db.session.commit()

            updated_report = update_report_status(
                report.id,
                "verified",
                admin.id
            )

            assert updated_report.status == "verified"

            history = ModerationHistory.query.filter_by(
                report_id=report.id
            ).first()

            assert history is not None
            assert history.admin_id == admin.id
            assert history.previous_status == "pending"
            assert history.new_status == "verified"

        finally:
            db.session.remove()
            db.drop_all()


# Tests that invalid status values are rejected.
def test_reject_invalid_report_status():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        try:
            citizen, admin = create_test_users()

            report = FloodReport(
                user_id=citizen.id,
                latitude=23.0225,
                longitude=72.5714,
                water_depth_cm=20,
                description="Test waterlogging report"
            )

            db.session.add(report)
            db.session.commit()

            with pytest.raises(ValueError):
                update_report_status(
                    report.id,
                    "approved",
                    admin.id
                )

            assert report.status == "pending"

            assert ModerationHistory.query.count() == 0

        finally:
            db.session.remove()
            db.drop_all()


# Tests that updating a nonexistent report returns None.
def test_update_nonexistent_report():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        try:
            _, admin = create_test_users()

            result = update_report_status(
                99999,
                "verified",
                admin.id
            )

            assert result is None

            assert ModerationHistory.query.count() == 0

        finally:
            db.session.remove()
            db.drop_all()