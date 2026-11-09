
from app.services.weather_service import validate_coordinates

test_cases = [
    (23.0225, 72.5714),
    (200, 72.5714),
    (23.0225, 250),
    ("Ahmedabad", 72.5714),
]

for latitude, longitude in test_cases:
    try:
        validate_coordinates(latitude, longitude)
        print(f"VALID: {latitude}, {longitude}")

    except ValueError as error:
        print(f"INVALID: {latitude}, {longitude}")
        print("Reason:", error)
