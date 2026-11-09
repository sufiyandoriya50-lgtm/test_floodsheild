
from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.models.user import User
from app.extensions import db


"""
 Decorator that allows access only to authenticated administrators.
"""
def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        # Verify the JWT access token.
        verify_jwt_in_request()

        # Get the authenticated user's ID.
        user_id = get_jwt_identity()

        # Find the user in the database.
        user = db.session.get(User, int(user_id))

        # Check whether the user has administrator privileges.
        if user is None or user.role != "admin":
            return jsonify({
                "status": "error",
                "message": "Administrator access required"
            }), 403

        return function(*args, **kwargs)

    return wrapper
