# location.py

from math import radians, sin, cos, sqrt, atan2


# ============================================================
# KNOWN MARINE LOCATIONS
# ============================================================

LOCATIONS = {

    "karwar": {
        "name": "Karwar",
        "latitude": 14.8167,
        "longitude": 74.1297
    },

    "goa": {
        "name": "Goa",
        "latitude": 15.2993,
        "longitude": 74.1240
    },

    "mangalore": {
        "name": "Mangalore",
        "latitude": 12.9141,
        "longitude": 74.8560
    },

    "malpe": {
        "name": "Malpe",
        "latitude": 13.3499,
        "longitude": 74.7037
    },

    "udupi": {
        "name": "Udupi",
        "latitude": 13.3409,
        "longitude": 74.7421
    },

    "kundapura": {
        "name": "Kundapura",
        "latitude": 13.6325,
        "longitude": 74.6905
    },

    "bhatkal": {
        "name": "Bhatkal",
        "latitude": 13.9850,
        "longitude": 74.7250
    },

    "honnavar": {
        "name": "Honnavar",
        "latitude": 14.2800,
        "longitude": 74.4440
    },

    "murudeshwar": {
        "name": "Murudeshwar",
        "latitude": 14.0940,
        "longitude": 74.4845
    },

    "kumta": {
        "name": "Kumta",
        "latitude": 14.4280,
        "longitude": 74.4180
    },

    "gokarna": {
        "name": "Gokarna",
        "latitude": 14.5479,
        "longitude": 74.3188
    }
}


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371.0  # Earth radius in km

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    dlat = lat2 - lat1
    dlon = radians(lon2) - radians(lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# ============================================================
# RESOLVE LOCATION
# ============================================================

def resolve_location(location):

    if not location:
        return {
            "error": "No location provided."
        }

    key = location.lower().strip()

    # --------------------------------------------------------
    # Exact location match
    # --------------------------------------------------------

    if key in LOCATIONS:

        result = LOCATIONS[key].copy()

        result["resolved"] = True
        result["match_type"] = "exact"

        return result


    # --------------------------------------------------------
    # Partial name matching
    # Example:
    # "kundapura beach"
    # "near kundapura"
    # --------------------------------------------------------

    for name, data in LOCATIONS.items():

        if name in key:

            result = data.copy()

            result["resolved"] = True
            result["match_type"] = "partial"

            return result


    # --------------------------------------------------------
    # Location not found
    # --------------------------------------------------------

    return {
        "resolved": False,
        "error": f"Location '{location}' not found.",
        "available_locations": [
            data["name"]
            for data in LOCATIONS.values()
        ]
    }


# ============================================================
# FIND NEAREST KNOWN LOCATION
# ============================================================

def find_nearest_location(latitude, longitude):

    nearest = None
    minimum_distance = float("inf")

    for name, data in LOCATIONS.items():

        distance = calculate_distance(
            latitude,
            longitude,
            data["latitude"],
            data["longitude"]
        )

        if distance < minimum_distance:

            minimum_distance = distance

            nearest = {
                "name": data["name"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "distance_km": round(distance, 2)
            }

    return nearest


# ============================================================
# GET LOCATION OR NEAREST MARINE LOCATION
# ============================================================

def get_location(location):

    result = resolve_location(location)

    if result.get("resolved"):

        return result

    return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_locations = [
        "Karwar",
        "Malpe",
        "Kundapura",
        "Kundapura Beach",
        "Murudeshwar",
        "UnknownPlace"
    ]

    for location in test_locations:

        print("\n----------------------------")
        print("Input:", location)

        result = resolve_location(location)

        print("Result:", result)