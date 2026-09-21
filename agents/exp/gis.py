import json
from pathlib import Path
from shapely.geometry import Point, shape


BASE_DIR = Path(__file__).resolve().parent
GEOJSON_FILE = BASE_DIR / "marine_zones.geojson"


def check_geofence(latitude, longitude):

    point = Point(longitude, latitude)

    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feature in data["features"]:

        geometry = shape(feature["geometry"])

        properties = feature.get("properties", {})

        if geometry.contains(point):

            return {
                "restricted": True,
                "zone": properties.get(
                    "name",
                    "Unknown zone"
                ),
                "type": properties.get(
                    "type",
                    "Restricted"
                )
            }

    return {
        "restricted": False,
        "zone": None,
        "type": None
    }


if __name__ == "__main__":

    latitude = 12.0
    longitude = 74.5

    result = check_geofence(
        latitude,
        longitude
    )

    print("=== GIS GEOFENCE ===")
    print(result)