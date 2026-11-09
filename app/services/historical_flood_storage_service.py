from app.extensions import db

from app.models.historical_flood_event import HistoricalFloodEvent

from app.services.historical_flood_service import (
    validate_historical_flood_event
)


def create_historical_flood_event(
    event_name,
    latitude,
    longitude,
    event_date,
    source,
    severity=None,
    water_depth_cm=None,
    description=None,
    source_reference=None
):
    """
    Validates and stores a historical flood event.
    """

    validated_data = validate_historical_flood_event(
        latitude=latitude,
        longitude=longitude,
        event_date=event_date,
        source=source,
        severity=severity,
        water_depth_cm=water_depth_cm
    )

    if event_name is not None and not isinstance(event_name, str):
        raise ValueError("Event name must be text")

    if description is not None and not isinstance(description, str):
        raise ValueError("Description must be text")

    if source_reference is not None and not isinstance(source_reference, str):
        raise ValueError("Source reference must be text")

    historical_event = HistoricalFloodEvent(
        event_name=event_name.strip() if event_name else None,
        latitude=validated_data["latitude"],
        longitude=validated_data["longitude"],
        event_date=validated_data["event_date"],
        water_depth_cm=validated_data["water_depth_cm"],
        severity=validated_data["severity"],
        description=description.strip() if description else None,
        source=validated_data["source"],
        source_reference=(
            source_reference.strip()
            if source_reference
            else None
        )
    )

    try:
        db.session.add(historical_event)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return historical_event