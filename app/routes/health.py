
from flask import Blueprint, jsonify


# Create the health-check blueprint
health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """
    Check whether the FloodShield backend is running.
    """

    return jsonify({
        "status": "success",
        "message": "FloodShield backend is running",
        "application": "FloodShield"
    }), 200
