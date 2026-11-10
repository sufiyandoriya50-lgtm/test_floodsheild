
"""
FloodShield database models.

All database models are imported here so that
SQLAlchemy and Flask-Migrate can discover them.
"""

from app.models.user import User
from app.models.flood_report import FloodReport
from app.models.weather_record import WeatherRecord
from app.models.risk_assessment import RiskAssessment
from app.models.report_media import FloodReportMedia
from app.models.historical_flood_event import HistoricalFloodEvent
from app.models.historical_weather_record import HistoricalWeatherRecord
from app.models.notification import Notification
from app.models.device_token import DeviceToken
from app.models.notification_preference import NotificationPreference
#this __all__ defines what will be impoterd whensomeone does  from app.models import *
__all__ = [
    "User",
    "FloodReport",
    "WeatherRecord",
    "RiskAssessment",
    "FloodReportMedia",
    "ModerationHistory",
    "HistoricalFloodEvent",
    "HistoricalWeatherRecord",
    "Notification",
    "DeviceToken",
    "NotificationPreference"
]
