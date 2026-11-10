
from app.utils.geo import calculate_distance_km

# Example locations in Ahmedabad.
location_1 = (23.0225, 72.5714)
location_2 = (23.0300, 72.5800)

distance = calculate_distance_km(
    location_1[0],
    location_1[1],
    location_2[0],
    location_2[1]
)

print(f"Distance: {distance:.3f} km")

# Basic correctness checks.
assert distance > 0
assert calculate_distance_km(
    23.0225, 72.5714,
    23.0225, 72.5714
) == 0

print("Geographic distance tests passed.")
