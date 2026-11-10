import os
import tempfile

import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.historical_flood_event import HistoricalFloodEvent
from app.services.historical_flood_import_service import (
    import_historical_flood_csv,
)


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_import_historical_flood_csv(app):
    with app.app_context():

        csv_content = """event_name,latitude,longitude,event_date,water_depth_cm,severity,description,source
Ahmedabad Flood 2023,23.0225,72.5714,2023-07-20T10:30:00+00:00,45,high,Heavy waterlogging,Official Dataset
Ahmedabad Flood 2022,23.0300,72.5800,2022-08-15T08:00:00+00:00,30,moderate,Road flooding,News Archive
Invalid Flood,200,72.5714,2023-07-20T10:30:00+00:00,20,high,Invalid coordinates,Test Source
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".csv",
            delete=False,
            newline="",
        ) as csv_file:
            csv_file.write(csv_content)
            csv_path = csv_file.name

        try:
            result = import_historical_flood_csv(csv_path)
            print("\nIMPORT RESULT:", result)

            assert result["imported_count"] == 2
            assert result["failed_count"] == 1
            assert result["failed_rows"][0]["row"] == 4

            saved_events = HistoricalFloodEvent.query.count()
            assert saved_events == 2

        finally:
            os.remove(csv_path)