from datetime import datetime, timezone

from app.extensions import db
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.device_token_service import register_device_token
from app.models.notification import Notification
from app.services.notification_preference_service import (
    get_or_create_preferences,
    update_notification_preferences
)

notifications_bp = Blueprint("notifications", __name__)



# POST /api/notifications/device-token
# Registers or updates the authenticated user's Firebase Installation ID.
@notifications_bp.route("/api/notifications/device-token", methods=["POST"])
@jwt_required()
# Handles registration of a mobile device for FloodShield push notifications.
def register_device():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON request body is required"
        }), 400

    fid = data.get("fid")
    platform = data.get("platform")

    try:
        user_id = int(get_jwt_identity())

        device = register_device_token(
            user_id=user_id,
            fid=fid,
            platform=platform
        )

        return jsonify({
            "status": "success",
            "message": "Device registered successfully",
            "device": {
                "id": device.id,
                "fid": device.fid,
                "platform": device.platform,
                "is_active": device.is_active
            }
        }), 201

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

# GET /api/notifications
# Retrieves the authenticated user's notification history with pagination and optional read-status filtering.
@notifications_bp.route("/api/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())

    # Read pagination parameters from the URL.
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    if page is None or page < 1:
        return jsonify({
            "status": "error",
            "message": "Page must be a positive integer"
        }), 400

    if per_page is None or per_page < 1 or per_page > 100:
        return jsonify({
            "status": "error",
            "message": "Per page must be between 1 and 100"
        }), 400

    # Start with notifications belonging only to the authenticated user.
    query = Notification.query.filter_by(user_id=user_id)

    # Optionally filter notifications by read status.
    read_filter = request.args.get("is_read")

    if read_filter is not None:
        if read_filter.lower() not in {"true", "false"}:
            return jsonify({
                "status": "error",
                "message": "is_read must be true or false"
            }), 400

        query = query.filter_by(
            is_read=read_filter.lower() == "true"
        )

    # Calculate the total number of matching notifications.
    total = query.count()

    # Retrieve the requested page, newest notifications first.
    notifications = (
        query
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return jsonify({
        "status": "success",
        "notifications": [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "risk_level": notification.risk_level,
                "latitude": notification.latitude,
                "longitude": notification.longitude,
                "is_read": notification.is_read,
                "delivery_status": notification.delivery_status,
                "created_at": (
                    notification.created_at.isoformat()
                    if notification.created_at else None
                ),
                "read_at": (
                    notification.read_at.isoformat()
                    if notification.read_at else None
                )
            }
            for notification in notifications
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }), 200


# PATCH /api/notifications/<notification_id>/read
# Marks a notification belonging to the authenticated user as read.
@notifications_bp.route(
    "/api/notifications/<int:notification_id>/read",
    methods=["PATCH"]
)
@jwt_required()
def mark_notification_as_read(notification_id):
    user_id = int(get_jwt_identity())

    # Retrieve only a notification owned by the authenticated user.
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user_id
    ).first()

    if notification is None:
        return jsonify({
            "status": "error",
            "message": "Notification not found"
        }), 404

    # Mark the notification as read only if it has not already been read.
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return jsonify({
        "status": "success",
        "message": "Notification marked as read",
        "notification": {
            "id": notification.id,
            "is_read": notification.is_read,
            "read_at": (
                notification.read_at.isoformat()
                if notification.read_at else None
            )
        }
    }), 200


# GET /api/notifications/preferences
# Retrieves the authenticated user's notification preferences.
@notifications_bp.route(
    "/api/notifications/preferences",
    methods=["GET"]
)
@jwt_required()
def get_user_notification_preferences():

    user_id = int(get_jwt_identity())

    try:
        preferences = get_or_create_preferences(user_id)

        return jsonify({
            "status": "success",
            "preferences": {
                "push_enabled": preferences.push_enabled,
                "high_risk_enabled": preferences.high_risk_enabled,
                "severe_risk_enabled": preferences.severe_risk_enabled
            }
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400


# PATCH /api/notifications/preferences
# Updates the authenticated user's notification preferences.
@notifications_bp.route(
    "/api/notifications/preferences",
    methods=["PATCH"]
)
@jwt_required()
def update_user_notification_preferences():

    user_id = int(get_jwt_identity())

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON"
        }), 400

    try:
        preferences = update_notification_preferences(
            user_id=user_id,
            updates=data
        )

        return jsonify({
            "status": "success",
            "message": "Notification preferences updated",
            "preferences": {
                "push_enabled": preferences.push_enabled,
                "high_risk_enabled": preferences.high_risk_enabled,
                "severe_risk_enabled": preferences.severe_risk_enabled
            }
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400
