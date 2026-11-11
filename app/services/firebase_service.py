
import os

import firebase_admin
from firebase_admin import credentials, auth


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


# Verifies a Firebase ID token and returns its trusted decoded claims.
def verify_firebase_id_token(id_token):

    # Validate the token input.
    if not isinstance(id_token, str) or not id_token.strip():
        raise ValueError("A valid Firebase ID token is required")

    # Ensure that Firebase Admin SDK has been initialized.
    try:
        firebase_app = firebase_admin.get_app()

    except ValueError as error:
        raise RuntimeError(
            "Firebase authentication is not configured"
        ) from error

    try:
        # Verify the signature, expiry, and revocation status.
        decoded_token = auth.verify_id_token(
            id_token.strip(),
            app=firebase_app,
            check_revoked=True
        )

        return decoded_token

    except (
        auth.InvalidIdTokenError,
        auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError,
        auth.UserDisabledError
    ) as error:

        raise ValueError(
            "Firebase ID token is invalid, expired, or revoked"
        ) from error

    except Exception as error:
        # Do not expose internal Firebase errors to API clients.
        raise RuntimeError(
            "Firebase token verification is temporarily unavailable"
        ) from error
