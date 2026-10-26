
import json
import math
import os
import re
from datetime import datetime, timezone

import requests
import searoute as sr
from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None


# ============================================================
# SAPTHA SAGARA — Marine Intelligence Agent
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

client = None

if GEMINI_API_KEY and genai is not None:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as exc:
        print(f"Gemini initialization failed: {exc}")


HEADERS = {
    "User-Agent": "SAPTHA-SAGARA-Marine-Intelligence/1.0"
}

LOCATION_ALIASES = {
    "mangalore": "Mangalore, Karnataka, India",
    "mangaluru": "Mangalore, Karnataka, India",
    "goa": "Goa, India",
    "panaji": "Panaji, Goa, India",
    "karwar": "Karwar, Karnataka, India",
    "udupi": "Udupi, Karnataka, India",
    "kundapura": "Kundapura, Karnataka, India",
    "bhatkal": "Bhatkal, Karnataka, India",
    "honnavar": "Honnavar, Karnataka, India",
    "kumta": "Kumta, Karnataka, India",
    "cochin": "Kochi, Kerala, India",
    "kochi": "Kochi, Kerala, India",
    "mumbai": "Mumbai, Maharashtra, India",
    "chennai": "Chennai, Tamil Nadu, India",
    "visakhapatnam": "Visakhapatnam, Andhra Pradesh, India",
    "vizag": "Visakhapatnam, Andhra Pradesh, India",
    "karnataka": "Karnataka, India",
    "kerala": "Kerala, India",
}


# ============================================================
# 1. LOCATION LOOKUP
# ============================================================

def get_location(location_name):
    """Resolve a place name to latitude and longitude."""

    if not location_name:
        return {"error": "Location name cannot be empty."}

    clean_name = str(location_name).strip()

    if not clean_name:
        return {"error": "Location name cannot be empty."}

    search_name = LOCATION_ALIASES.get(
        clean_name.lower(),
        clean_name if "india" in clean_name.lower()
        else f"{clean_name}, India"
    )

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": search_name,
        "format": "json",
        "limit": 1,
        "countrycodes": "in",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        results = response.json()

        if not results:
            return {
                "error": f"Could not find location: {clean_name}"
            }

        place = results[0]
        latitude = float(place["lat"])
        longitude = float(place["lon"])

        return {
            "name": place.get("display_name", clean_name),
            "latitude": latitude,
            "longitude": longitude,
            "coordinates": [latitude, longitude],
        }

    except (requests.RequestException, ValueError, KeyError) as exc:
        print(f"Location lookup failed: {exc}")
        return {
            "error": "Location service failed.",
            "details": str(exc),
        }


# ============================================================
# 2. LOCATION EXTRACTION FROM USER QUERY
# ============================================================

def extract_location(query):
    """Extract a supported place name from a marine query."""

    query_lower = query.lower()

    # Check longer place names first.
    aliases = sorted(
        LOCATION_ALIASES.keys(),
        key=len,
        reverse=True,
    )

    for alias in aliases:
        pattern = r"\b" + re.escape(alias) + r"\b"

        if re.search(pattern, query_lower):
            return alias

    # Attempt to handle queries such as:
    # "Check conditions near Murudeshwar"
    match = re.search(
        r"\b(?:near|at|around|off|coast of|coastal waters near)"
        r"\s+([a-zA-Z][a-zA-Z\s-]{1,40})",
        query,
        re.IGNORECASE,
    )

    if match:
        candidate = match.group(1).strip()

        candidate = re.split(
            r"\b(?:for|with|including|and|today|tomorrow|"
            r"right now|currently|,)\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        if candidate:
            return candidate

    return "Mangalore"


# ============================================================
# 3. FETCH WEATHER CONDITIONS
# ============================================================

def get_weather(latitude, longitude):
    """Fetch current weather from Open-Meteo."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "wind_gusts_10m"
        ),
        "timezone": "UTC",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20,
        )
        response.raise_for_status()

        result = response.json()

        return {
            "available": True,
            "source": "Open-Meteo",
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "current": result.get("current", {}),
            "units": result.get("current_units", {}),
        }

    except (requests.RequestException, ValueError) as exc:
        print(f"Weather retrieval failed: {exc}")

        return {
            "available": False,
            "source": "Open-Meteo",
            "error": str(exc),
        }


# ============================================================
# 4. FETCH MARINE CONDITIONS
# ============================================================

def get_marine_conditions(latitude, longitude):
    """Fetch available wave and marine observations/forecasts."""

    url = "https://marine-api.open-meteo.com/v1/marine"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "wave_height,"
            "wave_direction,"
            "wave_period"
        ),
        "timezone": "UTC",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20,
        )
        response.raise_for_status()

        result = response.json()

        return {
            "available": True,
            "source": "Open-Meteo Marine API",
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "current": result.get("current", {}),
            "units": result.get("current_units", {}),
            "note": (
                "Marine API values may be model-derived forecasts, "
                "not direct real-time buoy observations."
            ),
        }

    except (requests.RequestException, ValueError) as exc:
        print(f"Marine data retrieval failed: {exc}")

        return {
            "available": False,
            "source": "Open-Meteo Marine API",
            "error": str(exc),
        }


# ============================================================
# 5. GENERATE A GROUNDED MARINE SUMMARY
# ============================================================

def generate_summary(query, location, weather, marine):
    """Summarize retrieved data without inventing missing observations."""

    evidence = {
        "query": query,
        "location": location,
        "weather": weather,
        "marine_conditions": marine,
    }

    if client is not None:
        prompt = f"""
You are SAPTHA SAGARA, a marine intelligence assistant.

Answer the user's question using ONLY the supplied evidence.

Rules:
1. Do not invent weather readings, wave measurements, warnings,
   fishing advisories, or official government alerts.
2. Clearly identify unavailable data.
3. Distinguish model-derived data from official observations.
4. Do not claim that fishing is safe based only on these data.
5. If no official fishing advisory is supplied, say that an
   official advisory has not been verified.
6. Give practical, cautious guidance and mention the data time.
7. Do not present yourself as a substitute for official marine
   forecasts or coast guard instructions.

User question:
{query}

Retrieved evidence:
{json.dumps(evidence, indent=2, default=str)}
"""

        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            if getattr(response, "text", None):
                return response.text

        except Exception as exc:
            print(f"Gemini summary failed: {exc}")

    # Fallback: provide data without depending on Gemini.
    weather_current = weather.get("current", {})
    marine_current = marine.get("current", {})

    parts = [
        f"Marine conditions for {location.get('name', 'the requested area')}.",
        "These results are informational and are not an official safety clearance.",
    ]

    if weather.get("available"):
        parts.append(
            "Weather data: "
            + json.dumps(weather_current, default=str)
        )
    else:
        parts.append("Weather data is currently unavailable.")

    if marine.get("available"):
        parts.append(
            "Marine data: "
            + json.dumps(marine_current, default=str)
        )
    else:
        parts.append("Marine data is currently unavailable.")

    parts.append(
        "No official fishing advisory was verified by this request. "
        "Check relevant official marine forecasts and local authorities "
        "before making a trip."
    )

    return "\n\n".join(parts)


# ============================================================
# 6. MARINE QUERY ENTRY POINT — USED BY FASTAPI
# ============================================================

def run_agent(query):
    """Process a marine intelligence query and return structured data."""

    if not isinstance(query, str) or len(query.strip()) < 2:
        return {
            "success": False,
            "error": "Please provide a valid marine query.",
        }

    query = query.strip()
    place_name = extract_location(query)
    location = get_location(place_name)

    if location.get("error"):
        return {
            "success": False,
            "query": query,
            "requested_location": place_name,
            "error": location["error"],
            "details": location.get("details"),
        }

    latitude = location["latitude"]
    longitude = location["longitude"]

    weather = get_weather(latitude, longitude)
    marine = get_marine_conditions(latitude, longitude)

    summary = generate_summary(
        query,
        location,
        weather,
        marine,
    )

    return {
        "success": True,
        "query": query,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "location": location,
        "weather": weather,
        "marine_conditions": marine,
        "summary": summary,
        "limitations": [
            "Weather and marine data may be model-derived.",
            "No official fishing advisory is automatically verified.",
            "This output is not a certified navigation or safety system.",
        ],
    }


# ============================================================
# 7. ROUTE DISTANCE AND WAYPOINT HELPERS
# ============================================================

def calculate_distance(origin, destination):
    """Calculate straight-line distance between two coordinates in km."""

    lat1 = math.radians(origin[0])
    lon1 = math.radians(origin[1])
    lat2 = math.radians(destination[0])
    lon2 = math.radians(destination[1])

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    a = min(1.0, max(0.0, a))

    return 6371.0 * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )


def build_route_points(origin, destination, number_of_points=10):
    """Create interpolated waypoints, not a navigable sea route."""

    start_lat = origin[0]
    start_lon = origin[1]
    end_lat = destination[0]
    end_lon = destination[1]

    number_of_points = max(2, int(number_of_points))
    points = []

    for index in range(number_of_points):
        fraction = index / (number_of_points - 1)

        latitude = start_lat + fraction * (end_lat - start_lat)
        longitude = start_lon + fraction * (end_lon - start_lon)

        points.append({
            "sequence": index + 1,
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
        })

    return points


# ============================================================
# 8. ROUTE PLANNING ENTRY POINT — USED BY FASTAPI
# ============================================================

def run_route_planning(origin, destination):
    """Return a sea-route visualization estimate between two locations."""

    if not origin or not destination:
        return {
            "success": False,
            "error": "Origin and destination are required.",
        }

    origin_location = get_location(origin)
    destination_location = get_location(destination)

    if origin_location.get("error"):
        return {
            "success": False,
            "error": f"Origin lookup failed: {origin_location['error']}",
        }

    if destination_location.get("error"):
        return {
            "success": False,
            "error": (
                "Destination lookup failed: "
                f"{destination_location['error']}"
            ),
        }

    start = (
        origin_location["latitude"],
        origin_location["longitude"],
    )
    end = (
        destination_location["latitude"],
        destination_location["longitude"],
    )

    distance_km = calculate_distance(start, end)

    try:
        # searoute expects coordinates in [longitude, latitude] order.
        sea_route = sr.searoute(
            [start[1], start[0]],
            [end[1], end[0]],
            append_orig_dest=True,
        )

        coordinates = sea_route["geometry"]["coordinates"]
        route_distance_km = float(sea_route["properties"]["length"])

        # Leaflet expects each point as [latitude, longitude].
        waypoints = [
            {
                "sequence": index + 1,
                "latitude": round(float(coordinate[1]), 6),
                "longitude": round(float(coordinate[0]), 6),
            }
            for index, coordinate in enumerate(coordinates)
        ]

        route_type = "Sea-route visualization estimate"

    except Exception as exc:
        print(f"Sea-route generation failed: {type(exc).__name__}: {exc}")
        return {
            "success": False,
            "error": (
                "Unable to generate the sea-route estimate. "
                "Check backend logs."
            ),
        }

    return {
        "success": True,
        "origin": origin_location,
        "destination": destination_location,
        "straight_line_distance_km": round(distance_km, 2),
        "route_distance_km": round(route_distance_km, 2),
        "waypoints": waypoints,
        "route_type": route_type,
        "limitations": [
            "This is a route visualization estimate, not a certified navigational route.",
            "The route has not been verified against official nautical charts or current coastline data.",
            "Bathymetry, vessel draft, shipping restrictions, currents, weather, and official marine warnings are not evaluated.",
            "Do not use this result for operational navigation.",
        ],
    }


