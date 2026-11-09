from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.user import User
from app.services.report_service import create_flood_report


app = create_app(TestingConfig)

with app.app_context():
    db.create_all()

    user = User(
        name="Test User",
        email="reporttest@example.com"
    )
    user.set_password("test-password-123")

    db.session.add(user)
    db.session.commit()

    report = create_flood_report(
        user_id=user.id,
        latitude=23.0225,
        longitude=72.5714,
        water_depth_cm=25,
        description="Waterlogging near a residential road"
    )

    print("Report ID:", report.id)
    print("Latitude:", report.latitude)
    print("Longitude:", report.longitude)
    print("Water depth:", report.water_depth_cm)
    print("Status:", report.status)

    db.session.delete(report)
    db.session.delete(user)
    db.session.commit()

    db.drop_all()