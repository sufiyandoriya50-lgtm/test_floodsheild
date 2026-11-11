import math
import firebase_admin
from firebase_admin import messaging


from app.extensions import db
from app.models.user import User
from app.models.notification import Notification
from app.models.device_token import DeviceToken


# Saves a notification and attempts to deliver it to the user's active devices through Firebase.
def send_notification(
    user_id,
    title,
    message,
    notification_type="flood_alert",
    risk_level=None,
    latitude=None,
    longitude=None,
    deduplication_key=None
):
    # Validate the user ID.
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("A valid user ID is required")

    user = db.session.get(User, user_id)

    if user is None:
        raise ValueError("User does not exist")

    # Validate notification content.
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Notification title is required")

    if len(title.strip()) > 150:
        raise ValueError("Notification title cannot exceed 150 characters")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Notification message is required")

    if not isinstance(notification_type, str) or not notification_type.strip():
        raise ValueError("Notification type is required")

    if risk_level is not None:
        if risk_level not in {"low", "moderate", "high", "severe"}:
            raise ValueError("Invalid risk level")
        # Validate the optional deduplication key.
    if deduplication_key is not None:
        if not isinstance(deduplication_key, str):
            raise ValueError("Deduplication key must be a string")

        deduplication_key = deduplication_key.strip()

        if not deduplication_key:
            raise ValueError("Deduplication key cannot be empty")

        if len(deduplication_key) > 100:
            raise ValueError("Deduplication key cannot exceed 100 characters")
       # Validate optional coordinates.
    for coordinate_name, coordinate in (
        ("latitude", latitude),
        ("longitude", longitude)
    ):
        if coordinate is not None:
            if isinstance(coordinate, bool) or not isinstance(
                coordinate, (int, float)
            ):
                raise ValueError(f"{coordinate_name} must be numeric")

            if not math.isfinite(coordinate):
                raise ValueError(f"{coordinate_name} must be finite")

    if latitude is not None and not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if longitude is not None and not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")
    # Create the notification record before attempting delivery.
    notification = Notification(
        user_id=user_id,
        title=title.strip(),
        message=message.strip(),
        notification_type=notification_type.strip(),
        risk_level=risk_level,
        latitude=latitude,
        longitude=longitude,
        deduplication_key=deduplication_key,
        delivery_status="pending"
    )

    try:
        db.session.add(notification)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    # Find all active devices registered to this user.

    devices = DeviceToken.query.filter_by(
         user_id=user_id,
         is_active=True
        ).all()

     # Only devices with Firebase Installation IDs can receive FID-targeted messages.
    devices = [device for device in devices if device.fid]
    if not devices:
        notification.delivery_status = "no_devices"
        db.session.commit()
        return notification

    # Check whether Firebase has been initialized.
    try:
        firebase_app = firebase_admin.get_app()
    except ValueError:
        # Keep the notification pending until Firebase is configured.
        return notification

    successful_deliveries = 0

    # Send the notification separately to each registered device.
    for device in devices:
# Build a Firebase message for the registered device.
        firebase_message = messaging.Message(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.message
            ),
            data={
                "notification_id": str(notification.id),
                "notification_type": notification.notification_type,
                "risk_level": notification.risk_level or ""
            },
            fid=device.fid
        )
        try:
            messaging.send(
                firebase_message,
                app=firebase_app
            )
            successful_deliveries += 1
    
        except messaging.UnregisteredError:
            # Deactivate tokens that Firebase confirms are no longer registered.
            device.is_active = False
        
        except Exception:
            # Continue attempting delivery to the remaining devices.
            continue
    
    # Record the overall delivery outcome.
    if successful_deliveries == len(devices):
        notification.delivery_status = "sent"

    elif successful_deliveries > 0:
        notification.delivery_status = "partial"

    else:
        notification.delivery_status = "failed"

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return notification
