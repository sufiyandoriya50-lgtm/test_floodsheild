from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from app.models.user import User

auth_bp = Blueprint("auth", __name__)


# POST /api/auth/login
# Verifies a FloodShield citizen's email and password, then returns a JWT access token.
@auth_bp.route("/api/auth/login", methods=["POST"])
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

    # Use the same response for an unknown email and an incorrect password.
    if user is None or not user.check_password(password):
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