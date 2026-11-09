
import math


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates
    using the Haversine formula.

    Returns the distance in kilometers.
    """

    earth_radius_km = 6371.0

    # Convert degrees into radians.
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Calculate differences between coordinates.
    latitude_difference = lat2 - lat1
    longitude_difference = lon2 - lon1

    # Apply the Haversine formula.
    a = (
        math.sin(latitude_difference / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(longitude_difference / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = earth_radius_km * c

    return distance
