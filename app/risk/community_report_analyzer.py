
from datetime import datetime, timedelta, timezone
import math

from app.utils.geo import calculate_distance_km


# Initial engineering assumptions; these require local calibration.
DEFAULT_RADIUS_KM = 3.0
REPORT_FRESHNESS_DAYS = 7


"""
    Analyze verified community flood reports near a location.

    Recent reports and reports closer to the requested location
    contribute more strongly to the community risk signal.
    """
def analyze_community_reports(
    reports,
    latitude,
    longitude,
    radius_km=DEFAULT_RADIUS_KM,
    now=None,
):

    def validate_coordinate(value, name, minimum, maximum):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not minimum <= value <= maximum
        ):
            raise ValueError(f"{name} is invalid")

    validate_coordinate(latitude, "Latitude", -90, 90)
    validate_coordinate(longitude, "Longitude", -180, 180)

    if (
        isinstance(radius_km, bool)
        or not isinstance(radius_km, (int, float))
        or not math.isfinite(radius_km)
        or radius_km <= 0
    ):
        raise ValueError("Radius must be a positive number")

    if now is None:
        now = datetime.now(timezone.utc)

    if not isinstance(now, datetime):
        raise ValueError("now must be a datetime")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    now = now.astimezone(timezone.utc)

    if not reports:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "nearby_verified_reports": 0,
            "message": "No community reports are available.",
        }

    weighted_reports = []
    rejected_reports = 0

    for report in reports:

        # Only administrator-verified reports count as confirmed signals.
        if report.status != "verified":
            continue

        try:
            validate_coordinate(
                report.latitude,
                "Report latitude",
                -90,
                90,
            )
            validate_coordinate(
                report.longitude,
                "Report longitude",
                -180,
                180,
            )
        except ValueError:
            rejected_reports += 1
            continue

        distance = calculate_distance_km(
            latitude,
            longitude,
            report.latitude,
            report.longitude,
        )

        if distance > radius_km:
            continue

        created_at = report.created_at

        if not isinstance(created_at, datetime):
            rejected_reports += 1
            continue

        # SQLite may return naive UTC timestamps.
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        created_at = created_at.astimezone(timezone.utc)

        age = now - created_at

        if age < timedelta(0):
            rejected_reports += 1
            continue

        if age > timedelta(days=REPORT_FRESHNESS_DAYS):
            continue

        # More recent reports receive greater weight.
        recency_weight = math.exp(
            -age.total_seconds() / (REPORT_FRESHNESS_DAYS * 86400)
        )

        # Closer reports receive greater weight.
        distance_weight = max(
            0.0,
            1 - distance / radius_km
        )

        # Optional reported water depth contributes to severity.
        depth = report.water_depth_cm

        if depth is None:
            depth_score = 50
        elif (
            isinstance(depth, bool)
            or not isinstance(depth, (int, float))
            or not math.isfinite(depth)
            or depth < 0
        ):
            rejected_reports += 1
            continue
        elif depth < 10:
            depth_score = 25
        elif depth < 30:
            depth_score = 50
        elif depth < 60:
            depth_score = 75
        else:
            depth_score = 100

        weight = recency_weight * distance_weight

        weighted_reports.append((depth_score, weight))

    if not weighted_reports:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "nearby_verified_reports": 0,
            "observations_rejected": rejected_reports,
            "message": "No recent verified reports were found nearby.",
        }

    total_weight = sum(weight for _, weight in weighted_reports)

    if total_weight <= 0:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "nearby_verified_reports": len(weighted_reports),
            "message": "Community report weights could not be calculated.",
        }

    average_depth_score = (
        sum(score * weight for score, weight in weighted_reports)
        / total_weight
    )

    # Multiple independent verified reports increase the signal.
    report_count = len(weighted_reports)
    count_multiplier = min(1.0 + 0.15 * (report_count - 1), 1.6)

    final_score = min(
        100,
        round(average_depth_score * count_multiplier)
    )

    if final_score < 25:
        category = "low"
    elif final_score < 50:
        category = "moderate"
    elif final_score < 75:
        category = "high"
    else:
        category = "severe"

    return {
        "available": True,
        "score": final_score,
        "category": category,
        "nearby_verified_reports": report_count,
        "search_radius_km": radius_km,
        "message": (
            "Community risk signal calculated from recent "
            "verified flood reports."
        ),
    }
