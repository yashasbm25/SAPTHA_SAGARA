"""
SAPTHA SAGARA - Marine Route Engine

Purpose:
- Calculate direct route distance
- Generate candidate routes
- Evaluate route risk
- Detect restricted/high-risk route points
- Generate alternate routes
- Re-evaluate alternate routes
- Select the safer feasible route

IMPORTANT:
This is a marine decision-support prototype.
Generated waypoints are NOT certified navigational waypoints.
Do not use this engine for real-world navigation without
authoritative nautical charts, routing data, and safety validation.
"""

import math
from typing import Dict, List, Tuple


# ============================================================
# BASIC GEOGRAPHIC FUNCTIONS
# ============================================================

def calculate_distance(
    origin: Tuple[float, float],
    destination: Tuple[float, float]
) -> float:
    """
    Calculate great-circle distance between two coordinates.

    Coordinates:
        (latitude, longitude)

    Returns:
        Distance in kilometres.
    """

    lat1, lon1 = origin
    lat2, lon2 = destination

    earth_radius_km = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(earth_radius_km * c, 2)


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def check_route_risk(risk_score: float) -> Dict:
    """
    Convert a 0-100 risk score into a route risk category.
    """

    risk_score = max(0, min(100, float(risk_score)))

    if risk_score >= 75:
        level = "EXTREME"
        recommendation = "DO_NOT_TRAVEL"
        description = "Very high risk conditions detected."

    elif risk_score >= 50:
        level = "HIGH"
        recommendation = "CAUTION"
        description = "High risk conditions detected. Consider an alternative route."

    elif risk_score >= 25:
        level = "MODERATE"
        recommendation = "CAUTION"
        description = "Moderate risk conditions detected."

    else:
        level = "LOW"
        recommendation = "FAVORABLE"
        description = "Relatively favorable conditions."

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": level,
        "recommendation": recommendation,
        "description": description
    }


# ============================================================
# STRAIGHT-LINE WAYPOINT GENERATION
# ============================================================

def generate_waypoints(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    number_of_waypoints: int = 5
) -> List[Tuple[float, float]]:
    """
    Generate evenly spaced intermediate points between origin
    and destination.

    NOTE:
    These are geometric interpolation points, not certified
    navigational waypoints.
    """

    if number_of_waypoints < 0:
        number_of_waypoints = 0

    lat1, lon1 = origin
    lat2, lon2 = destination

    points = []

    for i in range(1, number_of_waypoints + 1):

        fraction = i / (number_of_waypoints + 1)

        lat = lat1 + (lat2 - lat1) * fraction
        lon = lon1 + (lon2 - lon1) * fraction

        points.append(
            (
                round(lat, 6),
                round(lon, 6)
            )
        )

    return points


def build_route_points(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    number_of_waypoints: int = 5
) -> List[Tuple[float, float]]:
    """
    Build complete route:

        origin
          ↓
       waypoint
          ↓
       waypoint
          ↓
       ...
          ↓
     destination
    """

    intermediate = generate_waypoints(
        origin,
        destination,
        number_of_waypoints
    )

    return [origin] + intermediate + [destination]


# ============================================================
# ROUTE SEGMENTS
# ============================================================

def calculate_route_segments(
    route_points: List[Tuple[float, float]]
) -> List[Dict]:
    """
    Calculate distance for every route segment.
    """

    segments = []

    for i in range(len(route_points) - 1):

        start = route_points[i]
        end = route_points[i + 1]

        distance = calculate_distance(start, end)

        segments.append({
            "segment": i + 1,
            "from": start,
            "to": end,
            "distance_km": distance
        })

    return segments


# ============================================================
# ROUTE RISK SUMMARY
# ============================================================

def calculate_route_risk_summary(
    origin_risk: float,
    destination_risk: float,
    restricted: bool = False,
    point_risks: List[float] = None
) -> Dict:
    """
    Calculate overall route risk.

    Strategy:
    - Restricted route => 100 / EXTREME
    - Otherwise use the highest meaningful point risk.
    - Endpoint risks are also considered.
    """

    if restricted:
        risk_score = 100

    else:

        scores = []

        if point_risks:
            scores.extend(point_risks)

        scores.append(float(origin_risk))
        scores.append(float(destination_risk))

        if scores:
            risk_score = max(scores)
        else:
            risk_score = 0

    return check_route_risk(risk_score)


# ============================================================
# ALTERNATE ROUTE GEOMETRY
# ============================================================

def _create_offset_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    offset_fraction: float,
    number_of_waypoints: int = 5
) -> List[Tuple[float, float]]:
    """
    Create a route offset perpendicular to the direct route.

    This is a prototype geometric alternative-route generator.

    Positive offset:
        one side of the direct route

    Negative offset:
        opposite side

    NOTE:
    This does NOT guarantee the route stays over navigable water.
    """

    lat1, lon1 = origin
    lat2, lon2 = destination

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Perpendicular vector
    perpendicular_lat = -delta_lon
    perpendicular_lon = delta_lat

    magnitude = math.sqrt(
        perpendicular_lat ** 2
        + perpendicular_lon ** 2
    )

    if magnitude == 0:
        return [origin, destination]

    perpendicular_lat /= magnitude
    perpendicular_lon /= magnitude

    # Scale offset relative to route length
    route_length = math.sqrt(
        delta_lat ** 2
        + delta_lon ** 2
    )

    offset_distance = route_length * offset_fraction

    offset_lat = perpendicular_lat * offset_distance
    offset_lon = perpendicular_lon * offset_distance

    intermediate = generate_waypoints(
        origin,
        destination,
        number_of_waypoints
    )

    alternate_points = []

    for lat, lon in intermediate:

        alternate_lat = lat + offset_lat
        alternate_lon = lon + offset_lon

        alternate_points.append(
            (
                round(alternate_lat, 6),
                round(alternate_lon, 6)
            )
        )

    return [origin] + alternate_points + [destination]


# ============================================================
# GENERATE MULTIPLE CANDIDATE ROUTES
# ============================================================

def generate_candidate_routes(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    number_of_waypoints: int = 5
) -> List[Dict]:
    """
    Generate:

    1. Direct route
    2. Alternate route on one side
    3. Alternate route on the opposite side
    """

    candidates = []

    direct_route = build_route_points(
        origin,
        destination,
        number_of_waypoints
    )

    candidates.append({
        "route_id": "DIRECT",
        "route_type": "DIRECT",
        "route_points": direct_route
    })

    # Moderate offset
    alternate_left = _create_offset_route(
        origin,
        destination,
        offset_fraction=0.12,
        number_of_waypoints=number_of_waypoints
    )

    candidates.append({
        "route_id": "ALTERNATE_A",
        "route_type": "ALTERNATE",
        "route_points": alternate_left
    })

    alternate_right = _create_offset_route(
        origin,
        destination,
        offset_fraction=-0.12,
        number_of_waypoints=number_of_waypoints
    )

    candidates.append({
        "route_id": "ALTERNATE_B",
        "route_type": "ALTERNATE",
        "route_points": alternate_right
    })

    return candidates


# ============================================================
# ROUTE EVALUATION
# ============================================================

def evaluate_route(
    route_points: List[Tuple[float, float]],
    point_analysis: List[Dict]
) -> Dict:
    """
    Evaluate an already-analyzed route.

    point_analysis should contain entries like:

    {
        "point": (...),
        "risk_score": 35,
        "risk_level": "MODERATE",
        "restricted": False
    }
    """

    restricted_points = [
        point
        for point in point_analysis
        if point.get("restricted", False)
    ]

    risk_scores = [
        float(point.get("risk_score", 0))
        for point in point_analysis
    ]

    route_distance = sum(
        calculate_distance(
            route_points[i],
            route_points[i + 1]
        )
        for i in range(len(route_points) - 1)
    )

    direct_distance = calculate_distance(
        route_points[0],
        route_points[-1]
    )

    if restricted_points:

        risk_score = 100
        risk_info = check_route_risk(risk_score)

        route_status = "BLOCKED"
        recommendation = "DO_NOT_TRAVEL"

    else:

        risk_score = max(risk_scores) if risk_scores else 0

        risk_info = check_route_risk(risk_score)

        route_status = "SAFE" if risk_score < 75 else "HIGH_RISK"

        recommendation = risk_info["recommendation"]

    return {
        "route_distance_km": round(route_distance, 2),
        "direct_distance_km": round(direct_distance, 2),
        "distance_difference_km": round(
            route_distance - direct_distance,
            2
        ),
        "risk_score": risk_info["risk_score"],
        "risk_level": risk_info["risk_level"],
        "recommendation": recommendation,
        "route_status": route_status,
        "restricted_points": restricted_points,
        "point_analysis": point_analysis
    }


# ============================================================
# SELECT BEST ROUTE
# ============================================================

def select_best_route(
    evaluated_routes: List[Dict]
) -> Dict:
    """
    Select the safest feasible route.

    Priority:

    1. Non-blocked routes
    2. Lowest risk
    3. Shorter distance
    """

    feasible_routes = [
        route
        for route in evaluated_routes
        if route.get("route_status") != "BLOCKED"
    ]

    if not feasible_routes:

        # If every route is blocked, return the least bad option
        return min(
            evaluated_routes,
            key=lambda route: (
                route.get("risk_score", 100),
                route.get("route_distance_km", float("inf"))
            )
        )

    return min(
        feasible_routes,
        key=lambda route: (
            route.get("risk_score", 100),
            route.get("route_distance_km", float("inf"))
        )
    )


# ============================================================
# ALTERNATE ROUTE GENERATION + RE-EVALUATION
# ============================================================

def generate_alternate_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    route_analyzer=None,
    number_of_waypoints: int = 5
) -> Dict:
    """
    Generate and evaluate direct + alternate routes.

    Parameters
    ----------
    origin:
        (latitude, longitude)

    destination:
        (latitude, longitude)

    route_analyzer:
        Optional callback used to evaluate each point.

        Expected:

            route_analyzer(point)

        to return:

            {
                "risk_score": 35,
                "risk_level": "MODERATE",
                "restricted": False,
                ...
            }

    If no analyzer is supplied, routes are generated but
    no real environmental risk data can be calculated.

    This separation allows agent.py to plug in its existing
    Weather + Ocean + GIS + Risk pipeline.
    """

    candidate_routes = generate_candidate_routes(
        origin,
        destination,
        number_of_waypoints
    )

    evaluated_routes = []

    for candidate in candidate_routes:

        route_points = candidate["route_points"]

        point_analysis = []

        if route_analyzer:

            for index, point in enumerate(route_points):

                try:

                    analysis = route_analyzer(point)

                    if analysis is None:
                        analysis = {}

                except Exception as error:

                    analysis = {
                        "risk_score": 100,
                        "risk_level": "UNKNOWN",
                        "restricted": False,
                        "error": str(error)
                    }

                point_analysis.append({
                    "point_index": index + 1,
                    "point": point,
                    **analysis
                })

        else:

            for index, point in enumerate(route_points):

                point_analysis.append({
                    "point_index": index + 1,
                    "point": point,
                    "risk_score": 0,
                    "risk_level": "UNKNOWN",
                    "restricted": False
                })

        evaluation = evaluate_route(
            route_points,
            point_analysis
        )

        evaluated_routes.append({
            **candidate,
            **evaluation
        })

    best_route = select_best_route(
        evaluated_routes
    )

    direct_route = next(
        (
            route
            for route in evaluated_routes
            if route["route_id"] == "DIRECT"
        ),
        None
    )

    alternate_used = (
        best_route["route_id"] != "DIRECT"
    )

    return {
        "origin": origin,
        "destination": destination,

        "selected_route": best_route,

        "selected_route_id": best_route["route_id"],

        "selected_route_type": best_route["route_type"],

        "alternate_route_used": alternate_used,

        "route_changed": alternate_used,

        "direct_route": direct_route,

        "candidate_routes": evaluated_routes,

        "routes_evaluated": len(evaluated_routes),

        "selection_reason": (
            "Alternative route selected because it provides "
            "a lower-risk feasible path."
            if alternate_used
            else
            "Direct route remains the best evaluated feasible route."
        ),

        "navigation_warning": (
            "Prototype decision-support route. "
            "Generated waypoints are not certified navigational waypoints."
        )
    }


# ============================================================
# COMPATIBLE MAIN ROUTE FUNCTION
# ============================================================

def generate_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    risk_score: float = 0,
    restricted: bool = False,
    origin_risk: float = 0,
    destination_risk: float = 0,
    number_of_waypoints: int = 5,
    alternate_route: bool = False,
    route_analyzer=None
) -> Dict:
    """
    Main route-generation function.

    Existing usage remains compatible:

        generate_route(
            origin,
            destination,
            risk_score=40,
            restricted=False
        )

    New capability:

        alternate_route=True

    with:

        route_analyzer=your_analysis_function

    """

    # --------------------------------------------------------
    # If route is already known to be restricted
    # --------------------------------------------------------

    if restricted:

        direct_points = build_route_points(
            origin,
            destination,
            number_of_waypoints
        )

        return {
            "status": "BLOCKED",
            "route_blocked": True,

            "origin": origin,
            "destination": destination,

            "distance_km": calculate_distance(
                origin,
                destination
            ),

            "direct_distance_km": calculate_distance(
                origin,
                destination
            ),

            "route_distance_km": calculate_distance(
                origin,
                destination
            ),

            "risk_score": 100,
            "risk_level": "EXTREME",

            "recommendation": "DO_NOT_TRAVEL",

            "route_points": direct_points,

            "segments": calculate_route_segments(
                direct_points
            ),

            "alternate_route_checked": alternate_route,

            "navigation_warning": (
                "Route blocked by restricted-area information. "
                "Do not use this prototype for real navigation."
            )
        }

    # --------------------------------------------------------
    # Alternate route mode
    # --------------------------------------------------------

    if alternate_route:

        alternate_result = generate_alternate_route(
            origin=origin,
            destination=destination,
            route_analyzer=route_analyzer,
            number_of_waypoints=number_of_waypoints
        )

        selected = alternate_result["selected_route"]

        return {
            "status": selected["route_status"],

            "route_blocked": (
                selected["route_status"] == "BLOCKED"
            ),

            "origin": origin,
            "destination": destination,

            "distance_km": selected[
                "route_distance_km"
            ],

            "direct_distance_km": selected[
                "direct_distance_km"
            ],

            "route_distance_km": selected[
                "route_distance_km"
            ],

            "distance_difference_km": selected[
                "distance_difference_km"
            ],

            "risk_score": selected[
                "risk_score"
            ],

            "risk_level": selected[
                "risk_level"
            ],

            "recommendation": selected[
                "recommendation"
            ],

            "route_points": selected[
                "route_points"
            ],

            "segments": calculate_route_segments(
                selected["route_points"]
            ),

            "route_id": selected[
                "route_id"
            ],

            "route_type": selected[
                "route_type"
            ],

            "alternate_route_checked": True,

            "alternate_route_used": alternate_result[
                "alternate_route_used"
            ],

            "route_changed": alternate_result[
                "route_changed"
            ],

            "routes_evaluated": alternate_result[
                "routes_evaluated"
            ],

            "direct_route": alternate_result[
                "direct_route"
            ],

            "candidate_routes": alternate_result[
                "candidate_routes"
            ],

            "selection_reason": alternate_result[
                "selection_reason"
            ],

            "navigation_warning": alternate_result[
                "navigation_warning"
            ]
        }

    # --------------------------------------------------------
    # Normal direct route mode
    # --------------------------------------------------------

    route_points = build_route_points(
        origin,
        destination,
        number_of_waypoints
    )

    segments = calculate_route_segments(
        route_points
    )

    risk_summary = calculate_route_risk_summary(
        origin_risk=origin_risk,
        destination_risk=destination_risk,
        restricted=False,
        point_risks=[risk_score]
    )

    route_distance = sum(
        segment["distance_km"]
        for segment in segments
    )

    return {
        "status": risk_summary["risk_level"],

        "route_blocked": False,

        "origin": origin,

        "destination": destination,

        "distance_km": calculate_distance(
            origin,
            destination
        ),

        "direct_distance_km": calculate_distance(
            origin,
            destination
        ),

        "route_distance_km": round(
            route_distance,
            2
        ),

        "distance_difference_km": round(
            route_distance
            - calculate_distance(origin, destination),
            2
        ),

        "risk_score": risk_summary[
            "risk_score"
        ],

        "risk_level": risk_summary[
            "risk_level"
        ],

        "recommendation": risk_summary[
            "recommendation"
        ],

        "route_points": route_points,

        "segments": segments,

        "route_id": "DIRECT",

        "route_type": "DIRECT",

        "alternate_route_checked": False,

        "alternate_route_used": False,

        "route_changed": False,

        "routes_evaluated": 1,

        "route_method": (
            "Geometric waypoint interpolation"
        ),

        "navigation_warning": (
            "Prototype decision-support route. "
            "Generated waypoints are not certified navigational waypoints."
        )
    }


# ============================================================
# DEMO / TEST
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("SAPTHA SAGARA - ROUTE ENGINE TEST")
    print("=" * 60)

    # Example:
    # Mangalore
    # Goa

    origin = (12.9141, 74.8560)
    destination = (15.4909, 73.8278)

    print("\nOrigin:")
    print(origin)

    print("\nDestination:")
    print(destination)

    print("\nDirect distance:")

    print(
        calculate_distance(
            origin,
            destination
        ),
        "km"
    )

    print("\nGenerating candidate routes...")

    result = generate_route(
        origin,
        destination,
        alternate_route=True,
        number_of_waypoints=5
    )

    print("\nRoutes evaluated:")
    print(
        result["routes_evaluated"]
    )

    print("\nSelected route:")
    print(
        result["route_id"]
    )

    print("\nRoute type:")
    print(
        result["route_type"]
    )

    print("\nRisk:")
    print(
        result["risk_level"]
    )

    print("\nRisk score:")
    print(
        result["risk_score"]
    )

    print("\nRoute distance:")
    print(
        result["route_distance_km"],
        "km"
    )

    print("\nRoute changed:")
    print(
        result["route_changed"]
    )

    print("\nSelection reason:")
    print(
        result["selection_reason"]
    )

    print("\nRoute points:")

    for i, point in enumerate(
        result["route_points"],
        start=1
    ):
        print(
            f"  {i}. {point}"
        )

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)