
import pytest

from app.services import firebase_service


# Verifies that Firebase initialization is skipped when no credentials are configured.
def test_initialize_firebase_without_credentials():

    result = firebase_service.initialize_firebase(None)

    assert result is None


# Verifies that a missing Firebase credentials file is rejected.
def test_initialize_firebase_rejects_missing_file(monkeypatch):

    monkeypatch.setattr(
        firebase_service.os.path,
        "isfile",
        lambda path: False
    )

    with pytest.raises(
        FileNotFoundError,
        match="Firebase service-account credentials file was not found"
    ):
        firebase_service.initialize_firebase(
            "missing-service-account.json"
        )


# Verifies that an existing Firebase application is reused.
def test_initialize_firebase_reuses_existing_app(monkeypatch):

    existing_app = object()

    monkeypatch.setattr(
        firebase_service.os.path,
        "isfile",
        lambda path: True
    )

    monkeypatch.setattr(
        firebase_service.firebase_admin,
        "get_app",
        lambda: existing_app
    )

    def unexpected_initialization(*args, **kwargs):
        pytest.fail("Firebase should reuse the existing application")

    monkeypatch.setattr(
        firebase_service.firebase_admin,
        "initialize_app",
        unexpected_initialization
    )

    result = firebase_service.initialize_firebase(
        "test-service-account.json"
    )

    assert result is existing_app


# Verifies that Firebase initializes when no application exists.
def test_initialize_firebase_creates_new_app(monkeypatch):

    credentials_object = object()
    firebase_app = object()

    monkeypatch.setattr(
        firebase_service.os.path,
        "isfile",
        lambda path: True
    )

    def no_existing_app():
        raise ValueError("Firebase app does not exist")

    monkeypatch.setattr(
        firebase_service.firebase_admin,
        "get_app",
        no_existing_app
    )

    monkeypatch.setattr(
        firebase_service.credentials,
        "Certificate",
        lambda path: credentials_object
    )

    initialized_arguments = []

    def mock_initialize_app(credentials):
        initialized_arguments.append(credentials)
        return firebase_app

    monkeypatch.setattr(
        firebase_service.firebase_admin,
        "initialize_app",
        mock_initialize_app
    )

    result = firebase_service.initialize_firebase(
        "test-service-account.json"
    )

    assert result is firebase_app
    assert initialized_arguments == [credentials_object]


# Verifies that Firebase ID token verification returns trusted claims.
def test_verify_firebase_id_token_success(monkeypatch):

    firebase_app = object()

    expected_claims = {
        "uid": "firebase-test-uid",
        "phone_number": "+919876543210"
    }

    monkeypatch.setattr(
        firebase_service.firebase_admin,
        "get_app",
        lambda: firebase_app
    )

    verification_arguments = []

    def mock_verify(token, app, check_revoked):
        verification_arguments.append(
            (token, app, check_revoked)
        )
        return expected_claims

    monkeypatch.setattr(
        firebase_service.auth,
        "verify_id_token",
        mock_verify
    )

    result = firebase_service.verify_firebase_id_token(
        " mock-firebase-token "
    )

    assert result == expected_claims

    assert verification_arguments == [
        ("mock-firebase-token", firebase_app, True)
    ]


# Verifies that empty Firebase ID tokens are rejected.
def test_verify_firebase_id_token_rejects_empty_token():

    with pytest.raises(
        ValueError,
        match="A valid Firebase ID token is required"
    ):
        firebase_service.verify_firebase_id_token("   ")


# Verifies that token verification fails safely when Firebase is not initialized.
def test_verify_firebase_id_token_without_initialized_app(monkeypatch):

    def no_initialized_app():
        raise ValueError("Firebase app does not exist")

    monkeypatch.setattr(
        firebase_service.firebase_admin,
        "get_app",
        no_initialized_app
    )

    with pytest.raises(
        RuntimeError,
        match="Firebase authentication is not configured"
    ):
        firebase_service.verify_firebase_id_token(
            "mock-firebase-token"
        )


# Verifies that unexpected Firebase verification errors are hidden from callers.
def test_verify_firebase_id_token_handles_unexpected_error(monkeypatch):

    monkeypatch.setattr(
        firebase_service.firebase_admin,
        "get_app",
        lambda: object()
    )

    def failed_verification(*args, **kwargs):
        raise Exception("Sensitive internal Firebase error")

    monkeypatch.setattr(
        firebase_service.auth,
        "verify_id_token",
        failed_verification
    )

    with pytest.raises(
        RuntimeError,
        match="Firebase token verification is temporarily unavailable"
    ) as error:
        firebase_service.verify_firebase_id_token(
            "mock-firebase-token"
        )

    assert "Sensitive internal Firebase error" not in str(error.value)
