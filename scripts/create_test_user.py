from app import create_app
from app.config import DevelopmentConfig
from app.extensions import db
from app.models.user import User


# Start the FloodShield application with development configuration
app = create_app(DevelopmentConfig)

with app.app_context():

    # Look for an existing test user
    user = User.query.filter_by(
        email="f3floodshield_test@example.com"
    ).first()

    if user is None:

        # Create a new test user
        user = User(
            name="FloodShield Test User",
            email="f3floodshield_test@example.com"
        )

        # Hash the password before storing it
        user.set_password("FloodTest123!")

        # Save the user in the development database
        db.session.add(user)
        db.session.commit()

        print("Test user created successfully!")

    else:
        print("Test user already exists!")

    print("User ID:", user.id)
    print("Email:", user.email)