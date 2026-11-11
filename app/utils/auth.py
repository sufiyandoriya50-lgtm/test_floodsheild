
from functools import wraps

from flask import jsonify
from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt_identity
)

from app.models.user import User
from app.extensions import db


# Restricts access to authenticated users with administrator privileges.
def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        # Verify the JWT access token.
        verify_jwt_in_request()

        # Retrieve the identity stored inside the JWT.
        user_id = get_jwt_identity()

        # Reject identities that cannot represent a database user ID.
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return jsonify({
                "status": "error",
                "message": "Administrator access required"
            }), 403

        # Retrieve the authenticated user from the database.
        user = db.session.get(User, user_id)

        # Reject missing users and non-administrator accounts.
        if user is None or user.role != "admin":
            return jsonify({
                "status": "error",
                "message": "Administrator access required"
            }), 403

        # Continue to the protected route.
        return function(*args, **kwargs)

    return wrapper
