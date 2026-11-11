from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from app.models.user import User
from sqlalchemy.exc import IntegrityError

from app.extensions import db , limiter
from app.services.firebase_service import verify_firebase_id_token
auth_bp = Blueprint("auth", __name__)


# POST /api/auth/login
# Verifies a FloodShield citizen's email and password, then returns a JWT access token.
@auth_bp.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json(silent=True)

    # Reject requests that do not contain a valid JSON object.
    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON"
        }), 400

    email = data.get("email")
    password = data.get("password")

    # Validate that both login fields are present and are strings.
    if (
        not isinstance(email, str)
        or not email.strip()
        or not isinstance(password, str)
        or not password
    ):
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    # Find the account using the supplied email address.
    user = User.query.filter_by(email=email.strip()).first()

    # Reject unknown accounts, incorrect passwords, and administrator accounts.
    if (
        user is None
        or not user.check_password(password)
        or user.role != "citizen"
    ):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401
    
    # JWT identity is stored as a string for compatibility.
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }), 200

# POST /api/auth/admin/login
# Authenticates administrators using their email address and password.
@auth_bp.route("/api/auth/admin/login", methods=["POST"])
@limiter.limit("5 per minute")
def admin_login():

    # Step 1: Retrieve the submitted JSON data.
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON"
        }), 400

    email = data.get("email")
    password = data.get("password")

    # Step 2: Validate the login fields.
    if (
        not isinstance(email, str)
        or not email.strip()
        or not isinstance(password, str)
        or not password
    ):
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    # Step 3: Find the administrator account.
    user = User.query.filter_by(
        email=email.strip()
    ).first()

    # Step 4: Reject invalid credentials and non-admin accounts.
    if (
        user is None
        or not user.check_password(password)
        or user.role != "admin"
    ):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401

    # Step 5: Generate a JWT for the authenticated administrator.
    access_token = create_access_token(
        identity=str(user.id)
    )

    # Step 6: Return the authentication response.
    return jsonify({
        "status": "success",
        "message": "Administrator login successful",
        "access_token": access_token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 200



# POST /api/auth/firebase
# Authenticates a citizen using a verified Firebase phone-authentication token.
@auth_bp.route("/api/auth/firebase", methods=["POST"])
@limiter.limit("10 per minute")
def firebase_login():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON"
        }), 400

    id_token = data.get("id_token")

    if not isinstance(id_token, str) or not id_token.strip():
        return jsonify({
            "status": "error",
            "message": "Firebase ID token is required"
        }), 400

    # Verify the Firebase identity.
    try:
        decoded_token = verify_firebase_id_token(id_token)

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid or expired Firebase authentication token"
        }), 401

    except RuntimeError:
        return jsonify({
            "status": "error",
            "message": "Firebase authentication is temporarily unavailable"
        }), 503

    firebase_uid = decoded_token.get("uid")
    phone_number = decoded_token.get("phone_number")

    if (
        not isinstance(firebase_uid, str)
        or not firebase_uid.strip()
        or not isinstance(phone_number, str)
        or not phone_number.strip()
    ):
        return jsonify({
            "status": "error",
            "message": "Verified Firebase account must contain a UID and phone number"
        }), 401

    firebase_uid = firebase_uid.strip()
    phone_number = phone_number.strip()

    # Find an account already linked to this Firebase identity.
    user = User.query.filter_by(
        firebase_uid=firebase_uid
    ).first()

    # Do not automatically link an existing account using phone number alone.
    if user is None:

        existing_phone_user = User.query.filter_by(
            phone_number=phone_number
        ).first()
        if existing_phone_user is not None:
        
            # Never allow administrator accounts to use citizen authentication.
            if existing_phone_user.role != "citizen":
                return jsonify({
                    "status": "error",
                    "message": "This account cannot use citizen authentication"
                }), 403
        
            # Existing citizen accounts require authenticated linking.
            return jsonify({
                "status": "error",
                "message": "Existing account requires authenticated Firebase linking"
            }), 409
        # Create a new citizen account.
        name = decoded_token.get("name")

        if not isinstance(name, str) or not name.strip():
            name = phone_number

        user = User(
            name=name.strip(),
            firebase_uid=firebase_uid,
            phone_number=phone_number,
            role="citizen"
        )

        try:
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            return jsonify({
                "status": "error",
                "message": "This Firebase account or phone number is already registered"
            }), 409

        except Exception:
            db.session.rollback()

            return jsonify({
                "status": "error",
                "message": "Unable to complete citizen authentication"
            }), 500

    else:

        # Reject administrator accounts.
        if user.role != "citizen":
            return jsonify({
                "status": "error",
                "message": "This account cannot use citizen authentication"
            }), 403

        # Require authenticated linking before changing an existing phone number.
        if (
            user.phone_number is not None
            and user.phone_number != phone_number
        ):
            return jsonify({
                "status": "error",
                "message": "Phone number change requires authenticated account linking"
            }), 409

        # Update the phone number if it was previously absent.
        if user.phone_number is None:

            conflicting_user = User.query.filter_by(
                phone_number=phone_number
            ).first()

            if conflicting_user is not None:
                return jsonify({
                    "status": "error",
                    "message": "This phone number is already registered"
                }), 409

            user.phone_number = phone_number

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()

                return jsonify({
                    "status": "error",
                    "message": "This phone number is already registered"
                }), 409

    # Issue the FloodShield access token.
    access_token = create_access_token(
        identity=str(user.id)
    )

    return jsonify({
        "status": "success",
        "message": "Citizen authentication successful",
        "access_token": access_token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "phone_number": user.phone_number,
            "role": user.role
        }
    }), 200


# POST /api/auth/firebase/link
# Links a verified Firebase phone identity to an already authenticated citizen account.
@auth_bp.route("/api/auth/firebase/link", methods=["POST"])
@limiter.limit("5 per minute")
@jwt_required()
def link_firebase_account():

    # Identify the currently authenticated FloodShield user.
    user_id = get_jwt_identity()

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Invalid authenticated user"
        }), 401

    user = db.session.get(User, user_id)

    if user is None or user.role != "citizen":
        return jsonify({
            "status": "error",
            "message": "Citizen account not found"
        }), 403

    # Validate the submitted Firebase ID token.
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON"
        }), 400

    id_token = data.get("id_token")

    if not isinstance(id_token, str) or not id_token.strip():
        return jsonify({
            "status": "error",
            "message": "Firebase ID token is required"
        }), 400

    # Verify the Firebase identity before linking it.
    try:
        decoded_token = verify_firebase_id_token(id_token)

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid or expired Firebase authentication token"
        }), 401

    except RuntimeError:
        return jsonify({
            "status": "error",
            "message": "Firebase authentication is temporarily unavailable"
        }), 503

    firebase_uid = decoded_token.get("uid")
    phone_number = decoded_token.get("phone_number")

    if (
        not isinstance(firebase_uid, str)
        or not firebase_uid.strip()
        or not isinstance(phone_number, str)
        or not phone_number.strip()
    ):
        return jsonify({
            "status": "error",
            "message": "Verified Firebase account must contain a UID and phone number"
        }), 401

    firebase_uid = firebase_uid.strip()
    phone_number = phone_number.strip()

    # Do not allow an existing Firebase identity to be replaced.
    if user.firebase_uid and user.firebase_uid != firebase_uid:
        return jsonify({
            "status": "error",
            "message": "This account is already linked to another Firebase identity"
        }), 409

    # Do not silently change an existing phone number.
    if user.phone_number and user.phone_number != phone_number:
        return jsonify({
            "status": "error",
            "message": "Phone number change requires a separate verified process"
        }), 409

    # Ensure another account does not already own this Firebase identity.
    existing_uid_user = User.query.filter_by(
        firebase_uid=firebase_uid
    ).first()

    if existing_uid_user is not None and existing_uid_user.id != user.id:
        return jsonify({
            "status": "error",
            "message": "This Firebase identity is already linked to another account"
        }), 409

    # Ensure another account does not already own this phone number.
    existing_phone_user = User.query.filter_by(
        phone_number=phone_number
    ).first()

    if existing_phone_user is not None and existing_phone_user.id != user.id:
        return jsonify({
            "status": "error",
            "message": "This phone number is already registered"
        }), 409

    # Save the verified Firebase identity to the authenticated account.
    user.firebase_uid = firebase_uid
    user.phone_number = phone_number

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "This Firebase identity or phone number is already registered"
        }), 409

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "Unable to link Firebase account"
        }), 500

    return jsonify({
        "status": "success",
        "message": "Firebase account linked successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "phone_number": user.phone_number,
            "role": user.role
        }
    }), 200
