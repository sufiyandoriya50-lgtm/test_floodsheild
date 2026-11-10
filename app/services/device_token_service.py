
from app.extensions import db
from app.models.device_token import DeviceToken
from app.models.user import User


# Registers or updates a Firebase Installation ID for a FloodShield user.
def register_device_token(user_id, fid, platform):

    # Validate the authenticated user's ID.
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("A valid user ID is required")

    user = db.session.get(User, user_id)

    if user is None:
        raise ValueError("User does not exist")

    # Validate the Firebase Installation ID.
    if not isinstance(fid, str) or not fid.strip():
        raise ValueError("A valid Firebase Installation ID is required")

    fid = fid.strip()

    if len(fid) > 512:
        raise ValueError("Firebase Installation ID is too long")

    # Validate the mobile platform.
    if not isinstance(platform, str):
        raise ValueError("Platform must be android or ios")

    platform = platform.strip().lower()

    if platform not in {"android", "ios"}:
        raise ValueError("Platform must be android or ios")

    # Check whether this installation is already registered.
    device = DeviceToken.query.filter_by(fid=fid).first()

    try:
        if device is not None:
            # Update the existing installation registration.
            device.user_id = user_id
            device.platform = platform
            device.is_active = True

        else:
            # Create a new FID-based device registration.
            device = DeviceToken(
                user_id=user_id,
                fid=fid,
                platform=platform,
                is_active=True
            )

            db.session.add(device)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return device
