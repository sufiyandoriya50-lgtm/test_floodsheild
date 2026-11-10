
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():

    email = input("Enter the account email to promote: ").strip()

    # Find the existing account.
    user = User.query.filter_by(email=email).first()

    if user is None:
        print("Error: User account not found.")
    else:
        # Promote the account to administrator.
        user.role = "admin"

        db.session.commit()

        print("\nAdministrator account created successfully.")
        print("Name:", user.name)
        print("Email:", user.email)
        print("Role:", user.role)
