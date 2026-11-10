
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.flood_report import FloodReport

app = create_app()

sample_reports = [
    {
        "latitude": 23.0225,
        "longitude": 72.5714,
        "water_depth_cm": 25,
        "description": "TEST DATA: Waterlogging near Ahmedabad city centre",
        "status": "pending"
    },
    {
        "latitude": 23.0240,
        "longitude": 72.5730,
        "water_depth_cm": 15,
        "description": "TEST DATA: Water accumulation near central road",
        "status": "pending"
    },
    {
        "latitude": 23.0300,
        "longitude": 72.5800,
        "water_depth_cm": 35,
        "description": "TEST DATA: Heavy waterlogging near riverfront area",
        "status": "verified"
    },
    {
        "latitude": 23.0390,
        "longitude": 72.5300,
        "water_depth_cm": 20,
        "description": "TEST DATA: Waterlogging near Vastrapur area",
        "status": "pending"
    },
    {
        "latitude": 22.9970,
        "longitude": 72.6020,
        "water_depth_cm": 40,
        "description": "TEST DATA: Water accumulation near Maninagar area",
        "status": "verified"
    }
]

with app.app_context():

    # Find the development test user.
    user = User.query.filter_by(
        email="floodshield_test@example.com"
    ).first()

    # Create the test user if it does not exist.
    if user is None:
        user = User(
            name="FloodShield Test User",
            email="floodshield_test@example.com"
        )
        user.set_password("FloodShieldTest123!")

        db.session.add(user)
        db.session.flush()

    created_count = 0

    for item in sample_reports:

        # Avoid inserting the same sample report twice.
        existing_report = FloodReport.query.filter_by(
            user_id=user.id,
            latitude=item["latitude"],
            longitude=item["longitude"],
            description=item["description"]
        ).first()

        if existing_report:
            continue

        report = FloodReport(
            user_id=user.id,
            latitude=item["latitude"],
            longitude=item["longitude"],
            water_depth_cm=item["water_depth_cm"],
            description=item["description"],
            status=item["status"]
        )

        db.session.add(report)
        created_count += 1

    try:
        db.session.commit()

        print("Sample data insertion completed.")
        print(f"Test User ID: {user.id}")
        print(f"New reports created: {created_count}")

        total_reports = FloodReport.query.count()
        print(f"Total reports in database: {total_reports}")

    except Exception as error:
        db.session.rollback()
        print("Error inserting sample reports:", error)
