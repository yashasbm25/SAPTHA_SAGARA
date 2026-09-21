def generate_fishing_advisory(weather, ocean, pfz, gis):
    """
    Deterministic Marine Risk & Fishing Advisory Engine.

    Produces:
    - 0-100 risk score
    - LOW / MODERATE / HIGH / EXTREME risk
    - warnings
    - fishing recommendation

    This is a prototype decision-support model.
    Official safety advisories should always take precedence.
    """

    risk_score = 0
    warnings = []

    # ---------------------------------------------------------
    # 1. GIS RESTRICTION
    # ---------------------------------------------------------

    if gis.get("restricted", False):
        return {
            "risk_score": 100,
            "risk_level": "EXTREME",
            "status": "DO_NOT_FISH",
            "recommendation": "Fishing is not recommended because the selected location is inside a restricted marine zone.",
            "warnings": ["Restricted marine zone detected."],
            "pfz_available": bool(pfz.get("zones")),
        }

    # ---------------------------------------------------------
    # 2. WEATHER RISK
    # ---------------------------------------------------------

    current_weather = weather.get("current", {})

    wind_speed = current_weather.get("wind_speed")
    precipitation = current_weather.get("precipitation")

    if wind_speed is not None:
        if wind_speed > 50:
            risk_score += 35
            warnings.append("Very high wind speed detected.")
        elif wind_speed > 35:
            risk_score += 25
            warnings.append("High wind speed detected.")
        elif wind_speed > 25:
            risk_score += 15
            warnings.append("Elevated wind speed detected.")
        elif wind_speed > 15:
            risk_score += 5

    if precipitation is not None:
        if precipitation > 10:
            risk_score += 15
            warnings.append("Heavy precipitation detected.")
        elif precipitation > 5:
            risk_score += 8
            warnings.append("Moderate precipitation detected.")

    # ---------------------------------------------------------
    # 3. OCEAN / WAVE RISK
    # ---------------------------------------------------------

    current_ocean = ocean.get("current", {})

    wave_height = current_ocean.get("wave_height")

    if wave_height is not None:
        if wave_height > 4:
            risk_score += 35
            warnings.append("Very high wave height detected.")
        elif wave_height > 3:
            risk_score += 25
            warnings.append("High wave height detected.")
        elif wave_height > 2:
            risk_score += 15
            warnings.append("Elevated wave height detected.")
        elif wave_height > 1:
            risk_score += 5

    # ---------------------------------------------------------
    # 4. PFZ INFORMATION
    # ---------------------------------------------------------

    pfz_zones = pfz.get("zones", [])

    pfz_available = len(pfz_zones) > 0

    if pfz_available:
        warnings.append("Potential Fishing Zone information is available from INCOIS.")
    else:
        warnings.append("No PFZ information was available for this query.")

    # ---------------------------------------------------------
    # 5. LIMIT SCORE
    # ---------------------------------------------------------

    risk_score = min(100, risk_score)

    # ---------------------------------------------------------
    # 6. CLASSIFY RISK
    # ---------------------------------------------------------

    if risk_score >= 75:
        risk_level = "EXTREME"
        status = "DO_NOT_FISH"
        recommendation = (
            "Fishing is not recommended under the detected marine conditions."
        )

    elif risk_score >= 50:
        risk_level = "HIGH"
        status = "CAUTION"
        recommendation = (
            "Fishing should be approached with high caution. "
            "Check official marine warnings before departure."
        )

    elif risk_score >= 25:
        risk_level = "MODERATE"
        status = "CAUTION"
        recommendation = (
            "Conditions require caution. Monitor weather and marine "
            "conditions before and during the trip."
        )

    else:
        risk_level = "LOW"
        status = "FAVORABLE"
        recommendation = (
            "No major risk factors were detected by this prototype "
            "decision engine."
        )

    # ---------------------------------------------------------
    # 7. FINAL RESULT
    # ---------------------------------------------------------

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "status": status,
        "recommendation": recommendation,
        "warnings": warnings,
        "pfz_available": pfz_available,
        "weather": {
            "wind_speed": wind_speed,
            "precipitation": precipitation,
        },
        "ocean": {
            "wave_height": wave_height,
        },
    }