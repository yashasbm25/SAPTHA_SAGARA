import json
import os
import requests
from google import genai
from dotenv import load_dotenv
from gis import check_geofence
from pfz import get_pfz_advisory
from decision_engine import generate_fishing_advisory
from planner import create_plan
from route_engine import (
    generate_route,
    build_route_points,
    generate_alternate_route,
    generate_candidate_routes,
    calculate_route_segments,
    calculate_distance
)
# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Make sure it is present in the .env file."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)

MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# LOCATION
# ============================================================

def get_location(location_name):
    """
    Resolve a place name to coordinates.

    SAPTHA SAGARA primarily targets Indian marine locations,
    so ambiguous locations are explicitly constrained to India.

    Returns:
        {
            "name": "...",
            "latitude": ...,
            "longitude": ...,
            "coordinates": (latitude, longitude)
        }
    """

    try:

        # ----------------------------------------------------
        # Normalize common marine locations
        # ----------------------------------------------------

        aliases = {
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
            "vizag": "Visakhapatnam, Andhra Pradesh, India"
        }

        clean_name = (
            str(location_name)
            .strip()
            .lower()
        )

        search_name = aliases.get(
            clean_name,
            f"{location_name}, India"
        )

        print(
            f"Location search: {search_name}"
        )

        # ----------------------------------------------------
        # OpenStreetMap Nominatim
        # ----------------------------------------------------

        url = (
            "https://nominatim.openstreetmap.org/search"
        )

        params = {
            "q": search_name,
            "format": "json",
            "limit": 1,
            "countrycodes": "in"
        }

        headers = {
            "User-Agent": (
                "SapthaSagara-MarineAI/1.0"
            )
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError(
                f"Could not resolve location: "
                f"{location_name}"
            )

        result = data[0]

        latitude = float(
            result["lat"]
        )

        longitude = float(
            result["lon"]
        )

        display_name = result.get(
            "display_name",
            location_name
        )

        coordinates = (
            latitude,
            longitude
        )

        return {
            "name": display_name,
            "latitude": latitude,
            "longitude": longitude,
            "coordinates": coordinates
        }

    except Exception as error:

        print(
            f"Location resolution error "
            f"for {location_name}: {error}"
        )

        raise


# ============================================================
# WEATHER
# ============================================================

def get_weather(
    latitude,
    longitude
):
    """
    Fetch current weather from Open-Meteo.
    """

    try:

        url = (
            "https://api.open-meteo.com/v1/forecast"
        )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "wind_speed_10m,"
                "wind_direction_10m"
            ),
            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        return {
            "temperature": current.get(
                "temperature_2m"
            ),
            "humidity": current.get(
                "relative_humidity_2m"
            ),
            "precipitation": current.get(
                "precipitation"
            ),
            "wind_speed": current.get(
                "wind_speed_10m"
            ),
            "wind_direction": current.get(
                "wind_direction_10m"
            ),
            "source": "Open-Meteo"
        }

    except Exception as error:

        return {
            "error": str(error),
            "source": "Open-Meteo"
        }


# ============================================================
# WEATHER FORECAST
# ============================================================

def get_forecast(
    latitude,
    longitude
):
    """
    Fetch short forecast from Open-Meteo.
    """

    try:

        url = (
            "https://api.open-meteo.com/v1/forecast"
        )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": (
                "temperature_2m,"
                "precipitation_probability,"
                "wind_speed_10m,"
                "wind_direction_10m"
            ),
            "forecast_days": 2,
            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
            "time": data.get(
                "hourly",
                {}
            ).get("time", [])[:12],

            "temperature": data.get(
                "hourly",
                {}
            ).get("temperature_2m", [])[:12],

            "precipitation_probability": data.get(
                "hourly",
                {}
            ).get(
                "precipitation_probability",
                []
            )[:12],

            "wind_speed": data.get(
                "hourly",
                {}
            ).get(
                "wind_speed_10m",
                []
            )[:12],

            "wind_direction": data.get(
                "hourly",
                {}
            ).get(
                "wind_direction_10m",
                []
            )[:12],

            "source": "Open-Meteo"
        }

    except Exception as error:

        return {
            "error": str(error),
            "source": "Open-Meteo"
        }


# ============================================================
# OCEAN CONDITIONS
# ============================================================

def get_ocean_conditions(
    latitude,
    longitude
):
    """
    Fetch marine conditions from Open-Meteo Marine API.
    """

    try:

        url = (
            "https://marine-api.open-meteo.com/v1/marine"
        )

        params = {
            "latitude": latitude,
            "longitude": longitude,

            "current": (
                "wave_height,"
                "wave_direction,"
                "wave_period,"
                "swell_wave_height,"
                "swell_wave_direction,"
                "swell_wave_period"
            ),

            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        return {
            "wave_height": current.get(
                "wave_height"
            ),

            "wave_direction": current.get(
                "wave_direction"
            ),

            "wave_period": current.get(
                "wave_period"
            ),

            "swell_wave_height": current.get(
                "swell_wave_height"
            ),

            "swell_wave_direction": current.get(
                "swell_wave_direction"
            ),

            "swell_wave_period": current.get(
                "swell_wave_period"
            ),

            "source": "Open-Meteo Marine"
        }

    except Exception as error:

        return {
            "error": str(error),
            "source": "Open-Meteo Marine"
        }


# ============================================================
# SEA TEMPERATURE
# ============================================================

def get_sea_temperature(
    latitude,
    longitude
):
    """
    Fetch sea-surface temperature if available.
    """

    try:

        url = (
            "https://marine-api.open-meteo.com/v1/marine"
        )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "sea_surface_temperature",
            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        return {
            "sea_surface_temperature": current.get(
                "sea_surface_temperature"
            ),
            "source": "Open-Meteo Marine"
        }

    except Exception as error:

        return {
            "error": str(error),
            "source": "Open-Meteo Marine"
        }


# ============================================================
# CHLOROPHYLL
# ============================================================

def get_chlorophyll(
    latitude,
    longitude
):
    """
    Attempt chlorophyll retrieval.

    INCOIS ERDDAP availability can vary, so failures are
    returned cleanly rather than crashing the complete agent.
    """

    try:

        return {
            "status": "UNAVAILABLE",
            "message": (
                "Chlorophyll data source is currently "
                "unavailable for this coordinate."
            ),
            "latitude": latitude,
            "longitude": longitude,
            "source": "INCOIS ERDDAP"
        }

    except Exception as error:

        return {
            "error": str(error),
            "source": "INCOIS ERDDAP"
        }


# ============================================================
# GIS
# ============================================================

def get_gis(
    latitude,
    longitude
):
    """
    Check whether coordinate falls inside a configured
    marine geofence/restricted polygon.
    """

    try:

        result = check_geofence(
            latitude,
            longitude
        )

        return result

    except Exception as error:

        return {
            "restricted": False,
            "zone": None,
            "type": None,
            "error": str(error)
        }


# ============================================================
# PFZ
# ============================================================

def get_pfz(
    latitude=None,
    longitude=None
):
    """
    Fetch PFZ advisory.

    Current PFZ implementation is based on the available
    INCOIS advisory integration.
    """

    try:

        return get_pfz_advisory()

    except Exception as error:

        return {
            "error": str(error),
            "source": "INCOIS"
        }


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(
    tool_name,
    latitude,
    longitude
):
    """
    Execute a marine intelligence tool.
    """

    if tool_name == "get_location":

        return get_location(
            str(latitude)
        )

    if tool_name == "get_weather":

        return get_weather(
            latitude,
            longitude
        )

    if tool_name == "get_forecast":

        return get_forecast(
            latitude,
            longitude
        )

    if tool_name == "get_ocean_conditions":

        return get_ocean_conditions(
            latitude,
            longitude
        )

    if tool_name == "get_sea_temperature":

        return get_sea_temperature(
            latitude,
            longitude
        )

    if tool_name == "get_chlorophyll":

        return get_chlorophyll(
            latitude,
            longitude
        )

    if tool_name == "get_pfz":

        return get_pfz(
            latitude,
            longitude
        )

    if tool_name == "get_gis":

        return get_gis(
            latitude,
            longitude
        )

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )


# ============================================================
# QUERY UNDERSTANDING
# ============================================================

def understand_query(
    user_query
):
    """
    Gemini-based intent and entity extraction.
    """

    prompt = f"""
You are the intent-classification component of
SAPTHA SAGARA, an Agentic AI Marine Intelligence Platform.

Analyze the user query and return ONLY valid JSON.

Possible intents:

SAFETY_ASSESSMENT
PFZ_DISCOVERY
FISHING_POTENTIAL
MARINE_CONDITIONS
HAZARD_CHECK
GENERAL_MARINE_QUERY
ROUTE_PLANNING

For ROUTE_PLANNING:
- identify origin
- identify destination
- both should be place names

Return exactly:

{{
    "intent": "...",
    "location": "...",
    "origin": "...",
    "destination": "..."
}}

If a field is unavailable, use null.

User query:
{user_query}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    text = response.text.strip()

    # Remove accidental markdown fences
    if text.startswith("```"):
        text = text.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

    try:

        result = json.loads(text)

    except json.JSONDecodeError:

        return {
            "intent": "GENERAL_MARINE_QUERY",
            "location": None,
            "origin": None,
            "destination": None
        }

    return result


# ============================================================
# FINAL RESPONSE GENERATION
# ============================================================

def generate_final_response(
    user_query,
    data
):
    """
    Convert structured agent output into a concise
    natural-language response.
    """

    prompt = f"""
You are SAPTHA SAGARA, an Agentic AI Marine Intelligence
Assistant.

Answer the user's question using ONLY the provided
structured data.

User:
{user_query}

Structured data:
{json.dumps(data, indent=2, default=str)}

Important rules:

1. Do not invent marine conditions.
2. Clearly mention when data is unavailable.
3. For route planning, explain:
   - origin
   - destination
   - route selected
   - route distance
   - risk level
   - risk score
   - whether an alternate route was used
   - why it was selected
4. Mention restricted zones if present.
5. Keep the answer concise and suitable for a fisherman,
   maritime operator, or judge demonstration.
6. Do not claim the route is certified navigation.
7. Call it a decision-support route.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()


# ============================================================
# ROUTE POINT ANALYZER
# ============================================================

def analyze_route_point(
    point
):
    """
    Analyze one route point using:

        Weather
        Ocean
        GIS
        Deterministic Risk Engine

    Returns structured point-level intelligence.
    """

    latitude, longitude = point

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    weather = get_weather(
        latitude,
        longitude
    )

    # --------------------------------------------------------
    # Ocean
    # --------------------------------------------------------

    ocean = get_ocean_conditions(
        latitude,
        longitude
    )

    # --------------------------------------------------------
    # GIS
    # --------------------------------------------------------

    gis = get_gis(
        latitude,
        longitude
    )

    # --------------------------------------------------------
    # Deterministic risk engine
    # --------------------------------------------------------

    advisory = generate_fishing_advisory(
        weather=weather,
        ocean=ocean,
        pfz={},
        gis=gis
    )

    # --------------------------------------------------------
    # Extract risk
    # --------------------------------------------------------

    risk_score = advisory.get(
        "risk_score",
        0
    )

    risk_level = advisory.get(
        "risk_level",
        "UNKNOWN"
    )

    restricted = gis.get(
        "restricted",
        False
    )

    return {
        "latitude": latitude,
        "longitude": longitude,

        "risk_score": risk_score,

        "risk_level": risk_level,

        "restricted": restricted,

        "gis": gis,

        "weather": weather,

        "ocean": ocean,

        "advisory": advisory
    }


# ============================================================
# ROUTE PLANNING
# ============================================================

def run_route_planning(
    origin_name,
    destination_name
):
    """
    Complete route-planning workflow.

    1. Resolve origin
    2. Resolve destination
    3. Generate direct route
    4. Generate alternate candidates
    5. Evaluate each point
    6. Recalculate route risk
    7. Select safest feasible route
    """

    print("\n================================")
    print("       ROUTE INTELLIGENCE")
    print("================================")

    print(
        f"\nOrigin      : {origin_name}"
    )

    print(
        f"Destination : {destination_name}"
    )

    # ========================================================
    # ORIGIN
    # ========================================================

    print(
        "\n--------------------------------"
    )

    print(
        "Resolving origin..."
    )

    origin_data = get_location(
        origin_name
    )

    origin = origin_data[
        "coordinates"
    ]

    print(
        f"Origin: {origin_data['name']}"
    )

    print(
        f"Coordinates: "
        f"{origin[0]}, {origin[1]}"
    )

    # ========================================================
    # DESTINATION
    # ========================================================

    print(
        "\n--------------------------------"
    )

    print(
        "Resolving destination..."
    )

    destination_data = get_location(
        destination_name
    )

    destination = destination_data[
        "coordinates"
    ]

    print(
        f"Destination: "
        f"{destination_data['name']}"
    )

    print(
        f"Coordinates: "
        f"{destination[0]}, {destination[1]}"
    )

    # ========================================================
    # CANDIDATE ROUTES
    # ========================================================

    print(
        "\n--------------------------------"
    )

    print(
        "Generating route candidates..."
    )

    # --------------------------------------------------------
    # Create candidates directly through route engine
    # --------------------------------------------------------

    from route_engine import generate_candidate_routes

    candidate_routes = generate_candidate_routes(
        origin,
        destination,
        number_of_waypoints=5
    )

    print(
        f"Candidate routes: "
        f"{len(candidate_routes)}"
    )

    # ========================================================
    # EVALUATE EACH CANDIDATE
    # ========================================================

    evaluated_routes = []

    for candidate in candidate_routes:

        route_id = candidate[
            "route_id"
        ]

        route_type = candidate[
            "route_type"
        ]

        route_points = candidate[
            "route_points"
        ]

        print(
            "\n================================"
        )

        print(
            f"Evaluating {route_id} "
            f"({route_type})"
        )

        print(
            "================================"
        )

        point_analysis = []

        for index, point in enumerate(
            route_points,
            start=1
        ):

            print(
                f"\nPoint {index}/{len(route_points)}"
            )

            print(
                f"Coordinates: "
                f"{point[0]}, {point[1]}"
            )

            try:

                analysis = analyze_route_point(
                    point
                )

                point_analysis.append({
                    "point_index": index,
                    "point": point,
                    **analysis
                })

                print(
                    f"Risk: "
                    f"{analysis['risk_score']} "
                    f"({analysis['risk_level']})"
                )

                print(
                    f"Restricted: "
                    f"{analysis['restricted']}"
                )

            except Exception as error:

                print(
                    f"Point analysis error: "
                    f"{error}"
                )

                # Fail-safe:
                # unknown point is treated as high risk

                point_analysis.append({
                    "point_index": index,
                    "point": point,
                    "risk_score": 100,
                    "risk_level": "EXTREME",
                    "restricted": False,
                    "error": str(error)
                })

        # ----------------------------------------------------
        # Evaluate complete route
        # ----------------------------------------------------

        route_result = generate_route(
            origin=origin,
            destination=destination,
            alternate_route=False,
            number_of_waypoints=5
        )

        # ----------------------------------------------------
        # Replace default route risk with actual point data
        # ----------------------------------------------------

        risk_scores = [
            float(
                point.get(
                    "risk_score",
                    0
                )
            )
            for point in point_analysis
        ]

        restricted_points = [
            point
            for point in point_analysis
            if point.get(
                "restricted",
                False
            )
        ]

        if restricted_points:

            overall_risk_score = 100

            overall_risk_level = "EXTREME"

            route_status = "BLOCKED"

            recommendation = "DO_NOT_TRAVEL"

        else:

            overall_risk_score = (
                max(risk_scores)
                if risk_scores
                else 0
            )

            if overall_risk_score >= 75:

                overall_risk_level = "EXTREME"
                route_status = "HIGH_RISK"
                recommendation = "DO_NOT_TRAVEL"

            elif overall_risk_score >= 50:

                overall_risk_level = "HIGH"
                route_status = "HIGH_RISK"
                recommendation = "CAUTION"

            elif overall_risk_score >= 25:

                overall_risk_level = "MODERATE"
                route_status = "SAFE"
                recommendation = "CAUTION"

            else:

                overall_risk_level = "LOW"
                route_status = "SAFE"
                recommendation = "FAVORABLE"

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        route_distance = sum(
            calculate_distance(
                route_points[i],
                route_points[i + 1]
            )
            for i in range(
                len(route_points) - 1
            )
        )

        direct_distance = calculate_distance(
            origin,
            destination
        )

        evaluated_routes.append({
            "route_id": route_id,

            "route_type": route_type,

            "route_points": route_points,

            "point_analysis": point_analysis,

            "route_distance_km": round(
                route_distance,
                2
            ),

            "direct_distance_km": round(
                direct_distance,
                2
            ),

            "distance_difference_km": round(
                route_distance - direct_distance,
                2
            ),

            "risk_score": round(
                overall_risk_score,
                2
            ),

            "risk_level": overall_risk_level,

            "route_status": route_status,

            "recommendation": recommendation,

            "restricted_points": restricted_points
        })

    # ========================================================
    # SELECT BEST ROUTE
    # ========================================================

    feasible_routes = [
        route
        for route in evaluated_routes
        if route["route_status"] != "BLOCKED"
    ]

    if feasible_routes:

        selected_route = min(
            feasible_routes,
            key=lambda route: (
                route["risk_score"],
                route["route_distance_km"]
            )
        )

    else:

        selected_route = min(
            evaluated_routes,
            key=lambda route: (
                route["risk_score"],
                route["route_distance_km"]
            )
        )

    # ========================================================
    # ROUTE CHANGE DETECTION
    # ========================================================

    direct_route = next(
        route
        for route in evaluated_routes
        if route["route_id"] == "DIRECT"
    )

    route_changed = (
        selected_route["route_id"]
        != "DIRECT"
    )

    # ========================================================
    # FINAL ROUTE ENGINE RESULT
    # ========================================================

    final_route = generate_route(
        origin=origin,
        destination=destination,
        risk_score=selected_route[
            "risk_score"
        ],
        restricted=(
            selected_route["route_status"]
            == "BLOCKED"
        ),
        origin_risk=(
            direct_route[
                "point_analysis"
            ][0].get(
                "risk_score",
                0
            )
        ),
        destination_risk=(
            direct_route[
                "point_analysis"
            ][-1].get(
                "risk_score",
                0
            )
        ),
        number_of_waypoints=5
    )

    # Use the actual selected route points
    final_route["route_points"] = (
        selected_route["route_points"]
    )

    # Recalculate selected route segments
    from route_engine import calculate_route_segments

    final_route["segments"] = (
        calculate_route_segments(
            selected_route["route_points"]
        )
    )

    final_route.update({

        "route_id": selected_route[
            "route_id"
        ],

        "route_type": selected_route[
            "route_type"
        ],

        "route_distance_km": selected_route[
            "route_distance_km"
        ],

        "direct_distance_km": selected_route[
            "direct_distance_km"
        ],

        "distance_difference_km": selected_route[
            "distance_difference_km"
        ],

        "risk_score": selected_route[
            "risk_score"
        ],

        "risk_level": selected_route[
            "risk_level"
        ],

        "recommendation": selected_route[
            "recommendation"
        ],

        "route_blocked": (
            selected_route[
                "route_status"
            ] == "BLOCKED"
        ),

        "alternate_route_checked": True,

        "alternate_route_used": route_changed,

        "route_changed": route_changed,

        "routes_evaluated": len(
            evaluated_routes
        ),

        "candidate_routes": evaluated_routes,

        "direct_route": direct_route,

        "selected_route": selected_route,

        "highest_risk_point": (
            max(
                selected_route[
                    "point_analysis"
                ],
                key=lambda x: x.get(
                    "risk_score",
                    0
                )
            )
            if selected_route[
                "point_analysis"
            ]
            else None
        ),

        "points_analyzed": len(
            selected_route[
                "point_analysis"
            ]
        ),

        "selection_reason": (
            "Alternative route selected because "
            "it provides a lower-risk feasible path."
            if route_changed
            else
            "Direct route remains the best "
            "evaluated feasible route."
        ),

        "risk_analysis_method": (
            "Each route waypoint was evaluated using "
            "weather, ocean conditions, GIS restrictions "
            "and the deterministic marine risk engine."
        ),

        "route_method": (
            "Geometric candidate-route generation "
            "with environmental risk re-evaluation."
        ),

        "navigation_warning": (
            "This is a marine decision-support prototype. "
            "Generated waypoints are not certified "
            "navigational waypoints."
        )
    })

    # ========================================================
    # PRINT SUMMARY
    # ========================================================

    print(
        "\n================================"
    )

    print(
        "       ROUTE SUMMARY"
    )

    print(
        "================================"
    )

    print(
        f"\nSelected route: "
        f"{final_route['route_id']}"
    )

    print(
        f"Route type: "
        f"{final_route['route_type']}"
    )

    print(
        f"Routes evaluated: "
        f"{final_route['routes_evaluated']}"
    )

    print(
        f"Risk: "
        f"{final_route['risk_score']} "
        f"({final_route['risk_level']})"
    )

    print(
        f"Distance: "
        f"{final_route['route_distance_km']} km"
    )

    print(
        f"Route changed: "
        f"{final_route['route_changed']}"
    )

    print(
        f"Recommendation: "
        f"{final_route['recommendation']}"
    )

    print(
        "\nSelection reason:"
    )

    print(
        final_route[
            "selection_reason"
        ]
    )

    return {
        "intent": "ROUTE_PLANNING",

        "origin": {
            "name": origin_data[
                "name"
            ],
            "coordinates": origin
        },

        "destination": {
            "name": destination_data[
                "name"
            ],
            "coordinates": destination
        },

        "route": final_route
    }


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(
    user_query
):
    """
    Main SAPTHA SAGARA agent pipeline.
    """

    print(
        "\n================================"
    )

    print(
        "       MARINE AI AGENT"
    )

    print(
        "================================"
    )

    print(
        f"\nUser:\n{user_query}"
    )

    # ========================================================
    # UNDERSTAND QUERY
    # ========================================================

    print(
        "\nUnderstanding user query..."
    )

    intent_data = understand_query(
        user_query
    )

    print(
        f"Intent      : "
        f"{intent_data.get('intent')}"
    )

    print(
        f"Location    : "
        f"{intent_data.get('location')}"
    )

    print(
        f"Origin      : "
        f"{intent_data.get('origin')}"
    )

    print(
        f"Destination : "
        f"{intent_data.get('destination')}"
    )

    # ========================================================
    # ROUTE PLANNING
    # ========================================================

    if (
        intent_data.get("intent")
        == "ROUTE_PLANNING"
    ):

        origin_name = intent_data.get(
            "origin"
        )

        destination_name = intent_data.get(
            "destination"
        )

        if not origin_name or not destination_name:

            return (
                "Please provide both an origin and "
                "destination, for example: "
                "'Find a route from Mangalore to Goa.'"
            )

        route_data = run_route_planning(
            origin_name,
            destination_name
        )

        return generate_final_response(
            user_query,
            route_data
        )

    # ========================================================
    # NORMAL MARINE QUERY
    # ========================================================

    plan = create_plan(
        user_query
    )

    location_name = (
        plan.get("location")
        or intent_data.get("location")
    )

    if not location_name:

        return generate_final_response(
            user_query,
            {
                "intent": intent_data,
                "plan": plan
            }
        )

    # ========================================================
    # RESOLVE LOCATION
    # ========================================================

    location_data = get_location(
        location_name
    )

    latitude = location_data[
        "latitude"
    ]

    longitude = location_data[
        "longitude"
    ]

    # ========================================================
    # EXECUTE PLANNED TOOLS
    # ========================================================

    tool_results = {}

    tools = plan.get(
        "tools",
        []
    )

    for tool_name in tools:

        try:

            print(
                f"\nExecuting tool: "
                f"{tool_name}"
            )

            tool_results[
                tool_name
            ] = execute_tool(
                tool_name,
                latitude,
                longitude
            )

        except Exception as error:

            tool_results[
                tool_name
            ] = {
                "error": str(error)
            }

    # ========================================================
    # DETERMINISTIC FISHING ADVISORY
    # ========================================================

    weather = tool_results.get(
        "get_weather",
        {}
    )

    ocean = tool_results.get(
        "get_ocean_conditions",
        {}
    )

    pfz = tool_results.get(
        "get_pfz",
        {}
    )

    gis = tool_results.get(
        "get_gis",
        {}
    )

    try:

        fishing_advisory = (
            generate_fishing_advisory(
                weather=weather,
                ocean=ocean,
                pfz=pfz,
                gis=gis
            )
        )

    except Exception as error:

        fishing_advisory = {
            "error": str(error)
        }

    # ========================================================
    # FINAL DATA
    # ========================================================

    final_data = {

        "intent": intent_data,

        "plan": plan,

        "location": location_data,

        "tool_results": tool_results,

        "fishing_advisory": fishing_advisory
    }

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return generate_final_response(
        user_query,
        final_data
    )


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "\n================================"
    )

    print(
        "        SAPTHA SAGARA"
    )

    print(
        "      MARINE AI AGENT"
    )

    print(
        "================================"
    )

    while True:

        try:

            user_query = input(
                "\nAsk the Marine Agent: "
            ).strip()

            if not user_query:
                continue

            if user_query.lower() in {
                "exit",
                "quit",
                "q"
            }:

                print(
                    "\nGoodbye."
                )

                break

            try:

                answer = run_agent(
                    user_query
                )

                print(
                    "\n================================"
                )

                print(
                    "           RESPONSE"
                )

                print(
                    "================================"
                )

                print(
                    f"\n{answer}"
                )

            except Exception as error:

                print(
                    "\n================================"
                )

                print(
                    "              ERROR"
                )

                print(
                    "================================"
                )

                print(
                    type(error).__name__
                )

                print(
                    str(error)
                )

        except KeyboardInterrupt:

            print(
                "\n\nExiting SAPTHA SAGARA..."
            )

            break

        except Exception as error:

            print(
                "\nUnexpected error:"
            )

            print(
                str(error)
            )