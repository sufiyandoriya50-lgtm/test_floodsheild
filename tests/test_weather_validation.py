import pytest

from app.services.weather_service import validate_coordinates


def test_valid_coordinates():
    validate_coordinates(23.0225, 72.5714)


def test_latitude_too_high():
    with pytest.raises(ValueError):
        validate_coordinates(95, 72.5714)


def test_latitude_too_low():
    with pytest.raises(ValueError):
        validate_coordinates(-95, 72.5714)


def test_longitude_too_high():
    with pytest.raises(ValueError):
        validate_coordinates(23.0225, 190)


def test_longitude_too_low():
    with pytest.raises(ValueError):
        validate_coordinates(23.0225, -190)


def test_boolean_coordinates_rejected():
    with pytest.raises(ValueError):
        validate_coordinates(True, 72.5714)


def test_infinite_coordinates_rejected():
    with pytest.raises(ValueError):
        validate_coordinates(23.0225, float("inf"))