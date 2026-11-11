
import pytest

from app.extensions import db
from app.models.user import User


# Creates a citizen account for Firebase authentication tests.
def create_citizen(phone_number="+919876543210"):

    user = User(
        name="Test Citizen",
        phone_number=phone_number,
        role="citizen"
    )

    db.session.add(user)
    db.session.commit()

    return user


# Verifies that a new citizen can authenticate using Firebase.
def test_firebase_login_creates_new_citizen(
    client,
    app,
    monkeypatch
):

    from app.routes import auth

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "firebase-test-uid-001",
            "phone_number": "+919876543210",
            "name": "Firebase Citizen"
        }
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["token_type"] == "Bearer"
    assert data["user"]["name"] == "Firebase Citizen"
    assert data["user"]["phone_number"] == "+919876543210"
    assert data["user"]["role"] == "citizen"
    assert data["access_token"]

    with app.app_context():
        user = User.query.filter_by(
            firebase_uid="firebase-test-uid-001"
        ).first()

        assert user is not None
        assert user.phone_number == "+919876543210"
        assert user.email is None
        assert user.password_hash is None



# Verifies that existing accounts require authenticated Firebase linking.
def test_firebase_login_rejects_automatic_account_linking(
    client,
    app,
    monkeypatch
):

    from app.routes import auth

    with app.app_context():
        create_citizen()

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "firebase-test-uid-002",
            "phone_number": "+919876543210"
        }
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 409

    assert response.get_json()["message"] == (
        "Existing account requires authenticated Firebase linking"
    )


# Verifies that an authenticated citizen can link a Firebase identity.
def test_authenticated_citizen_can_link_firebase_account(
    client,
    app,
    monkeypatch
):

    from app.routes import auth
    from flask_jwt_extended import create_access_token

    with app.app_context():
        user = User(
            name="Existing Citizen",
            email="existing_citizen@example.com",
            role="citizen"
        )

        user.set_password("CitizenPassword123")

        db.session.add(user)
        db.session.commit()

        user_id = user.id

        access_token = create_access_token(
            identity=str(user_id)
        )

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "firebase-linked-uid-001",
            "phone_number": "+919876543214"
        }
    )

    response = client.post(
        "/api/auth/firebase/link",
        json={"id_token": "mock-firebase-token"},
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    with app.app_context():
        linked_user = db.session.get(User, user_id)

        assert linked_user.firebase_uid == "firebase-linked-uid-001"
        assert linked_user.phone_number == "+919876543214"

# Verifies that an existing Firebase citizen can log in again.
def test_firebase_login_reuses_existing_account(
    client,
    app,
    monkeypatch
):

    from app.routes import auth

    with app.app_context():
        user = User(
            name="Existing Firebase Citizen",
            firebase_uid="firebase-test-uid-003",
            phone_number="+919876543211",
            role="citizen"
        )

        db.session.add(user)
        db.session.commit()

        original_user_id = user.id

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "firebase-test-uid-003",
            "phone_number": "+919876543211"
        }
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 200

    assert response.get_json()["user"]["id"] == original_user_id


# Verifies that invalid Firebase tokens are rejected.
def test_firebase_login_rejects_invalid_token(
    client,
    monkeypatch
):

    from app.routes import auth

    def reject_token(token):
        raise ValueError("Invalid Firebase token")

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        reject_token
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "invalid-token"}
    )

    assert response.status_code == 401


# Verifies that missing Firebase configuration produces a service error.
def test_firebase_login_handles_unavailable_service(
    client,
    monkeypatch
):

    from app.routes import auth

    def unavailable_service(token):
        raise RuntimeError("Firebase unavailable")

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        unavailable_service
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 503


# Verifies that Firebase login rejects a missing ID token.
def test_firebase_login_rejects_missing_token(client):

    response = client.post(
        "/api/auth/firebase",
        json={}
    )

    assert response.status_code == 400


# Verifies that Firebase login rejects tokens without a verified phone number.
def test_firebase_login_rejects_missing_phone_number(
    client,
    monkeypatch
):

    from app.routes import auth

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "firebase-test-uid-004"
        }
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 401




# Verifies that administrator accounts cannot use citizen authentication.
def test_firebase_login_rejects_administrator_account(
    client,
    app,
    monkeypatch
):

    from app.routes import auth

    with app.app_context():
        admin = User(
            name="Test Administrator",
            email="firebase_admin_test@example.com",
            phone_number="+919876543212",
            role="admin"
        )

        admin.set_password("AdminPassword123")

        db.session.add(admin)
        db.session.commit()

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "firebase-admin-test-uid",
            "phone_number": "+919876543212"
        }
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 403

# Verifies that an existing Firebase account cannot be linked to another UID.
def test_firebase_login_rejects_conflicting_firebase_uid(
    client,
    app,
    monkeypatch
):

    from app.routes import auth

    with app.app_context():
        user = User(
            name="Existing Citizen",
            firebase_uid="original-firebase-uid",
            phone_number="+919876543213",
            role="citizen"
        )

        db.session.add(user)
        db.session.commit()

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "different-firebase-uid",
            "phone_number": "+919876543213"
        }
    )

    response = client.post(
        "/api/auth/firebase",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 409
# Verifies that Firebase account linking requires a FloodShield JWT.
def test_firebase_link_rejects_unauthenticated_request(client):

    response = client.post(
        "/api/auth/firebase/link",
        json={"id_token": "mock-firebase-token"}
    )

    assert response.status_code == 401


# Verifies that administrators cannot link Firebase citizen identities.
def test_firebase_link_rejects_administrator(
    client,
    app
):

    from flask_jwt_extended import create_access_token

    with app.app_context():
        admin = User(
            name="Link Test Administrator",
            email="link_admin@example.com",
            role="admin"
        )

        admin.set_password("AdminPassword123")

        db.session.add(admin)
        db.session.commit()

        access_token = create_access_token(
            identity=str(admin.id)
        )

    response = client.post(
        "/api/auth/firebase/link",
        json={"id_token": "mock-firebase-token"},
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403


# Verifies that an existing Firebase UID cannot be linked to another citizen.
def test_firebase_link_rejects_uid_owned_by_another_account(
    client,
    app,
    monkeypatch
):

    from app.routes import auth
    from flask_jwt_extended import create_access_token

    with app.app_context():
        existing_user = User(
            name="First Citizen",
            firebase_uid="already-used-firebase-uid",
            phone_number="+919876543215",
            role="citizen"
        )

        target_user = User(
            name="Second Citizen",
            role="citizen"
        )

        db.session.add_all([existing_user, target_user])
        db.session.commit()

        access_token = create_access_token(
            identity=str(target_user.id)
        )

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "already-used-firebase-uid",
            "phone_number": "+919876543216"
        }
    )

    response = client.post(
        "/api/auth/firebase/link",
        json={"id_token": "mock-firebase-token"},
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 409


# Verifies that a phone number owned by another account cannot be linked.
def test_firebase_link_rejects_phone_owned_by_another_account(
    client,
    app,
    monkeypatch
):

    from app.routes import auth
    from flask_jwt_extended import create_access_token

    with app.app_context():
        existing_user = User(
            name="Phone Owner",
            phone_number="+919876543217",
            role="citizen"
        )

        target_user = User(
            name="Link Target",
            role="citizen"
        )

        db.session.add_all([existing_user, target_user])
        db.session.commit()

        access_token = create_access_token(
            identity=str(target_user.id)
        )

    monkeypatch.setattr(
        auth,
        "verify_firebase_id_token",
        lambda token: {
            "uid": "new-firebase-uid-for-link-test",
            "phone_number": "+919876543217"
        }
    )

    response = client.post(
        "/api/auth/firebase/link",
        json={"id_token": "mock-firebase-token"},
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 409