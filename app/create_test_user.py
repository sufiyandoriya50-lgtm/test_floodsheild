from getpass import getpass

from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    email = "floodshield_test@example.com"

    # Find the existing test account, or create it if it doesn't exist.
    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            name="FloodShield Test User",
            email=email
        )
        db.session.add(user)

    # Ask for a new password without displaying it on screen.
    password = getpass("Enter a new test account password: ")
    confirm_password = getpass("Confirm the password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")

    elif password != confirm_password:
        print("Passwords do not match.")

    else:
        user.set_password(password)
        db.session.commit()

        print("Test account created or updated successfully.")
        print("Email:", email)
        print("You can now use this account to test login.")