
from getpass import getpass

from app import create_app
from app.extensions import db
from app.models.user import User


# Creates a new administrator account through a trusted local command.
def create_admin_account():

    app = create_app()

    with app.app_context():

        # Collect administrator details.
        name = input("Enter administrator name: ").strip()
        email = input("Enter administrator email: ").strip().lower()

        if not name or not email:
            print("Name and email are required.")
            return

        # Refuse to modify an existing account.
        existing_user = User.query.filter_by(email=email).first()

        if existing_user is not None:
            print("An account with this email already exists.")
            print("No account or role was changed.")
            return

        # Request a password securely.
        password = getpass("Enter administrator password: ")
        confirm_password = getpass("Confirm administrator password: ")

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        # Create a new administrator account.
        admin = User(
            name=name,
            email=email,
            role="admin"
        )

        admin.set_password(password)

        try:
            db.session.add(admin)
            db.session.commit()

            print("Administrator account created successfully.")
            print("Email:", email)

        except Exception:
            db.session.rollback()
            print("Administrator account creation failed.")
            raise


if __name__ == "__main__":
    create_admin_account()
