
from datetime import datetime, timedelta, timezone

from app.models.flood_report import FloodReport
from app.models.notification import Notification
from app.services.notification_service import send_notification
from app.utils.geo import calculate_distance_km
from app.services.notification_preference_service import (
    get_or_create_preferences
)


# Defines the severity order used to decide whether a new alert is an escalation.
RISK_SEVERITY = {
    "low": 1,
    "moderate": 2,
    "high": 3,
    "severe": 4
}

# Prevents duplicate alerts for six hours.
ALERT_COOLDOWN_HOURS = 6


# Checks whether a similar or more severe alert was recently created for a user.
def is_duplicate_alert(user_id, deduplication_key, new_risk_level):

    cutoff_time = datetime.now(timezone.utc) - timedelta(
        hours=ALERT_COOLDOWN_HOURS
    )

    previous_notification = (
        Notification.query
        .filter_by(
            user_id=user_id,
            deduplication_key=deduplication_key,
            notification_type="flood_alert"
        )
        .order_by(Notification.created_at.desc())
        .first()
    )

    if previous_notification is None:
        return False

    previous_time = previous_notification.created_at

    if previous_time is None:
        return False

    # SQLite may return timestamps without timezone information.
    if previous_time.tzinfo is None:
        previous_time = previous_time.replace(tzinfo=timezone.utc)

    if previous_time < cutoff_time:
        return False

    previous_severity = RISK_SEVERITY.get(
        previous_notification.risk_level,
        0
    )

    new_severity = RISK_SEVERITY.get(new_risk_level, 0)

    # Suppress the alert if an equal or more severe alert was recently created.
    return previous_severity >= new_severity


# Sends risk alerts to users who submitted verified reports near an assessed location.
def send_nearby_risk_alerts(
    latitude,
    longitude,
    risk_level,
    radius_km=3
):
    if risk_level not in {"high", "severe"}:
        return {
            "status": "skipped",
            "reason": "Risk level does not require an automatic alert",
            "notifications_created": 0,
            "duplicates_skipped": 0
        }

    # Retrieve verified community reports.
    reports = FloodReport.query.filter_by(
        status="verified"
    ).all()

    # Identify unique users with reports inside the alert radius.
    nearby_user_ids = set()

    for report in reports:
        distance = calculate_distance_km(
            latitude,
            longitude,
            report.latitude,
            report.longitude
        )

        if distance <= radius_km:
            nearby_user_ids.add(report.user_id)

    notifications_created = 0
    duplicates_skipped = 0
    failed_users = []

    # Create one alert per eligible user, unless a duplicate is detected.
    for user_id in nearby_user_ids:
        # Retrieve this user's notification preferences.
        preferences = get_or_create_preferences(user_id)

        # Respect the user's master push-notification setting.
        if not preferences.push_enabled:
            continue

        # Respect the preference for the current risk severity.
        if risk_level == "high" and not preferences.high_risk_enabled:
            continue

        if risk_level == "severe" and not preferences.severe_risk_enabled:
            continue

        deduplication_key = (
            f"flood_alert:{user_id}:"
            f"{round(latitude, 3)}:{round(longitude, 3)}"
        )

        if is_duplicate_alert(
            user_id,
            deduplication_key,
            risk_level
        ):
            duplicates_skipped += 1
            continue

        if risk_level == "severe":
            title = "Severe Flood Risk Alert"
            message = (
                "Severe flood risk has been detected near a location "
                "where you previously submitted a flood report. "
                "Stay alert and follow local authority instructions."
            )
        else:
            title = "High Flood Risk Alert"
            message = (
                "High flood risk has been detected near a location "
                "where you previously submitted a flood report. "
                "Please remain cautious."
            )

        try:
            send_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type="flood_alert",
                risk_level=risk_level,
                latitude=latitude,
                longitude=longitude,
                deduplication_key=deduplication_key
            )

            notifications_created += 1

        except Exception:
            failed_users.append(user_id)

    return {
        "status": "completed",
        "risk_level": risk_level,
        "radius_km": radius_km,
        "eligible_users": len(nearby_user_ids),
        "notifications_created": notifications_created,
        "duplicates_skipped": duplicates_skipped,
        "failed_users": failed_users
    }
