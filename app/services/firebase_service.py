
import os
import firebase_admin
from firebase_admin import credentials


# Initializes Firebase Admin SDK using the service-account credentials.
def initialize_firebase(credentials_path):
    # Firebase is optional until credentials are configured.
    if not credentials_path:
        return None

    # Confirm that the credentials file actually exists.
    if not os.path.isfile(credentials_path):
        raise FileNotFoundError(
            "Firebase service-account credentials file was not found"
        )

    # Reuse the existing Firebase app if it has already been initialized.
    try:
        return firebase_admin.get_app()

    except ValueError:
        # Load the service-account credentials.
        firebase_credentials = credentials.Certificate(credentials_path)

        # Initialize Firebase Admin SDK.
        firebase_app = firebase_admin.initialize_app(firebase_credentials)

        return firebase_app
