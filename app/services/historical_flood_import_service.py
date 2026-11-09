import csv

from app.services.historical_flood_storage_service import (
    create_historical_flood_event,
)


"""
    Imports historical flood events from a CSV file.

    Valid rows are saved to the database.
    Invalid rows are recorded in the error report.
    """
def import_historical_flood_csv(file_path):

    imported_count = 0
    failed_rows = []

    with open(file_path, mode="r", encoding="utf-8-sig", newline="") as csv_file:

        reader = csv.DictReader(csv_file)

        required_columns = {
            "event_name",
            "latitude",
            "longitude",
            "event_date",
            "water_depth_cm",
            "severity",
            "description",
            "source",
        }

        if not reader.fieldnames or not required_columns.issubset(
            set(reader.fieldnames)
        ):
            raise ValueError("CSV file is missing required columns")

        for row_number, row in enumerate(reader, start=2):
            try:
                water_depth_text = row["water_depth_cm"].strip()

                water_depth = (
                     float(water_depth_text)
                     if water_depth_text
                     else None
                     )
                create_historical_flood_event(
                    event_name=row["event_name"].strip() or None,
                    # Convert CSV coordinate strings into floating-point numbers.
                    latitude=float(row["latitude"].strip()),
                    longitude=float(row["longitude"].strip()),
                    event_date=row["event_date"].strip(),
                    water_depth_cm=water_depth,
                    severity=row["severity"].strip() or None,
                    description=row["description"].strip() or None,
                    source=row["source"].strip(),
                )

                imported_count += 1

            except (ValueError, TypeError) as error:
                failed_rows.append({
                    "row": row_number,
                    "error": str(error),
                })

    return {
        "imported_count": imported_count,
        "failed_count": len(failed_rows),
        "failed_rows": failed_rows,
    }