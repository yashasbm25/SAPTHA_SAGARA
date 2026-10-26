
"""
SAPTHA SAGARA — Evidence Agent
Purpose:
- Track evidence returned by marine data agents.
- Record source, retrieval time, and data availability.
- Provide source references for AI-generated explanations.
- Flag missing, stale, or unavailable data.

Important:
This agent does not invent evidence or certify navigation decisions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json


# Maximum age before data is flagged as potentially stale.
DEFAULT_MAX_AGE_MINUTES = 60


def utc_now() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(timestamp: Optional[str]):
    """Parse an ISO timestamp; return None if invalid or missing."""
    if not timestamp:
        return None

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed
    except (ValueError, TypeError):
        return None


def check_freshness(
    retrieved_at: Optional[str],
    max_age_minutes: int = DEFAULT_MAX_AGE_MINUTES,
) -> Dict[str, Any]:
    """Check whether evidence is recent enough for the configured threshold."""

    retrieved_time = _parse_timestamp(retrieved_at)

    if retrieved_time is None:
        return {
            "freshness": "UNKNOWN",
            "age_minutes": None,
            "message": "Retrieval timestamp missing or invalid.",
        }

    age_seconds = (
        datetime.now(timezone.utc) - retrieved_time
    ).total_seconds()

    age_minutes = max(0, round(age_seconds / 60, 2))

    return {
        "freshness": (
            "FRESH"
            if age_minutes <= max_age_minutes
            else "STALE"
        ),
        "age_minutes": age_minutes,
        "message": (
            "Evidence is within the configured age limit."
            if age_minutes <= max_age_minutes
            else "Evidence may be outdated; refresh before relying on it."
        ),
    }


def create_evidence(
    data_type: str,
    result: Any,
    source: str,
    retrieved_at: Optional[str] = None,
    source_url: Optional[str] = None,
    location: Optional[str] = None,
    max_age_minutes: int = DEFAULT_MAX_AGE_MINUTES,
) -> Dict[str, Any]:
    """
    Wrap a tool result in a standard evidence record.

    Pass the actual result returned by the relevant agent/API.
    Do not pass guessed or fabricated observations.
    """

    retrieved_at = retrieved_at or utc_now()

    if isinstance(result, dict):
        explicitly_unavailable = (
            result.get("available") is False
            or str(result.get("status", "")).upper()
            in {"UNAVAILABLE", "ERROR", "FAILED"}
        )
    else:
        explicitly_unavailable = result is None

    if explicitly_unavailable:
        status = "UNAVAILABLE"
    elif result is None:
        status = "UNAVAILABLE"
    else:
        status = "AVAILABLE"

    freshness = check_freshness(
        retrieved_at,
        max_age_minutes=max_age_minutes,
    )

    return {
        "evidence_id": (
            f"{data_type.lower()}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
        ),
        "data_type": data_type,
        "source": source,
        "source_url": source_url,
        "location": location,
        "retrieved_at": retrieved_at,
        "status": status,
        "freshness": freshness["freshness"],
        "age_minutes": freshness["age_minutes"],
        "freshness_message": freshness["message"],
        "data": result if status == "AVAILABLE" else None,
        "limitations": (
            ["Data unavailable; do not infer missing measurements."]
            if status == "UNAVAILABLE"
            else []
        ),
    }


def build_evidence_report(
    evidence_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a report containing evidence, source references, and limitations."""

    available = [
        item for item in evidence_items
        if item.get("status") == "AVAILABLE"
    ]

    unavailable = [
        item for item in evidence_items
        if item.get("status") != "AVAILABLE"
    ]

    stale = [
        item for item in available
        if item.get("freshness") == "STALE"
    ]

    unknown_freshness = [
        item for item in available
        if item.get("freshness") == "UNKNOWN"
    ]

    sources = []
    seen_sources = set()

    for item in evidence_items:
        source = item.get("source")

        if source and source not in seen_sources:
            seen_sources.add(source)
            sources.append({
                "source": source,
                "source_url": item.get("source_url"),
            })

    limitations = []

    if unavailable:
        limitations.append(
            "Some requested data sources did not provide usable data."
        )

    if stale:
        limitations.append(
            "Some available evidence is older than the configured freshness limit."
        )

    if unknown_freshness:
        limitations.append(
            "Some evidence has no valid retrieval timestamp."
        )

    if not evidence_items:
        limitations.append("No evidence was supplied to the Evidence Agent.")

    return {
        "generated_at": utc_now(),
        "evidence_count": len(evidence_items),
        "available_count": len(available),
        "unavailable_count": len(unavailable),
        "stale_count": len(stale),
        "unknown_freshness_count": len(unknown_freshness),
        "sources": sources,
        "evidence": evidence_items,
        "limitations": limitations,
        "navigation_warning": (
            "This report documents evidence provenance. "
            "It does not certify a route as safe for navigation."
        ),
    }


def format_evidence_for_llm(
    report: Dict[str, Any],
) -> str:
    """
    Format evidence for inclusion in a Gemini prompt.

    The model must treat unavailable data as missing, not as zero.
    """

    instructions = """
EVIDENCE RULES:
1. Use only supplied evidence for claims about current conditions.
2. Identify the source when making a source-dependent claim.
3. Do not invent measurements, timestamps, citations, or API results.
4. Distinguish observed data from estimates and recommendations.
5. Treat UNAVAILABLE data as missing, never as zero.
6. Flag stale or uncertain evidence.
7. Do not claim a route is safe based on this report alone.
"""

    return (
        instructions
        + "\n\nEVIDENCE REPORT:\n"
        + json.dumps(report, indent=2, ensure_ascii=False, default=str)
    )


def save_evidence_report(
    report: Dict[str, Any],
    output_path: str = "evidence_report.json",
) -> str:
    """Save a report locally for debugging or audit purposes."""

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return output_path


if __name__ == "__main__":
    # Demonstration using explicitly labelled sample data.
    # Replace this sample with actual API/agent output in production.

    sample_weather = {
        "available": True,
        "temperature": 28,
        "wind_speed": 12,
    }

    weather_evidence = create_evidence(
        data_type="weather",
        result=sample_weather,
        source="DEMO DATA — NOT A LIVE API RESULT",
        location="Example location",
        max_age_minutes=60,
    )

    report = build_evidence_report([weather_evidence])

    print(json.dumps(report, indent=2, ensure_ascii=False))
