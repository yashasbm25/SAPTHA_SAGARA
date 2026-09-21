# planner.py
from dotenv import load_dotenv

load_dotenv()
"""
SAPTHA SAGARA
Marine Agentic AI - LLM Planner

Role:
    Convert natural-language marine queries into structured
    execution plans using Gemini.

The planner does NOT execute tools.
It only decides:
    - user intent
    - location
    - time context
    - required tools
"""


import os
import json
from google import genai


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# AVAILABLE TOOLS
# ============================================================

AVAILABLE_TOOLS = {
    "get_location":
        "Resolve a user-provided location into latitude and longitude.",

    "get_weather":
        "Get current weather conditions including temperature, wind and rainfall.",

    "get_forecast":
        "Get future weather forecast including wind and precipitation probability.",

    "get_ocean_conditions":
        "Get wave height, wave direction and wave period.",

    "get_sea_temperature":
        "Get sea surface temperature.",

    "get_chlorophyll":
        "Get satellite chlorophyll concentration.",

    "get_pfz":
        "Get INCOIS Potential Fishing Zone advisories.",

    "get_gis":
        "Check whether a location is inside a restricted/geofenced marine zone.",
    "find_safe_route":
            "Find the safe route."
}


# ============================================================
# PLANNER PROMPT
# ============================================================

PLANNER_PROMPT = """
You are the Planning Agent of SAPTHA SAGARA,
an Agentic AI Marine Intelligence Platform.

Your job is to analyze the user's natural-language query
and create a structured execution plan.

You MUST decide:

1. User intent
2. Location mentioned by the user
3. Time information
4. Which tools are required

Available tools:

get_location:
Resolve a user-provided location into latitude and longitude.

get_weather:
Get current weather conditions.

get_forecast:
Get future weather forecast.

get_ocean_conditions:
Get wave height, wave direction and wave period.

get_sea_temperature:
Get sea surface temperature.

get_chlorophyll:
Get satellite chlorophyll concentration.

get_pfz:
Get INCOIS Potential Fishing Zone advisories.

get_gis:
Check marine geofence/restricted zones.


Possible intents include:

SAFETY_ASSESSMENT
PFZ_DISCOVERY
FISHING_POTENTIAL
MARINE_CONDITIONS
HAZARD_CHECK
ROUTE_PLANNING
GENERAL_MARINE_QUERY

Rules:

- If a location is mentioned, extract its name exactly.
- Do NOT restrict locations to a predefined list.
- Users may mention ANY city, village, coastal area or marine location.
- If a location is required, always include get_location.
- For fishing safety, normally use weather, forecast, ocean conditions and GIS.
- For PFZ questions, use get_pfz.
- For fishing productivity, use PFZ, sea temperature and chlorophyll.
- For marine conditions, use weather, forecast and ocean conditions.
- For hazard questions, use weather, forecast, ocean conditions and GIS.
- For route planning, use location, forecast, ocean conditions and GIS.
- Only select tools that are relevant.
- Do not execute tools.
- Return ONLY valid JSON.

Return exactly this structure:

{
    "intent": "...",
    "location": "...",
    "time": "...",
    "tools": [
        "tool_name"
    ],
    "reasoning": "Short explanation of why these tools are required."
}

If no location is mentioned, use null.

If no specific time is mentioned, use "current".

User query:

"""


# ============================================================
# CREATE PLAN USING GEMINI
# ============================================================

def create_plan(user_query):

    prompt = PLANNER_PROMPT + user_query

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    text = response.text.strip()

    # --------------------------------------------------------
    # Remove markdown JSON fences if Gemini adds them
    # --------------------------------------------------------

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    # --------------------------------------------------------
    # Convert JSON text → Python dictionary
    # --------------------------------------------------------

    try:
        plan = json.loads(text)

    except json.JSONDecodeError:

        return {
            "error": "Planner returned invalid JSON.",
            "raw_response": text
        }

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    if "intent" not in plan:
        plan["intent"] = "GENERAL_MARINE_QUERY"

    if "location" not in plan:
        plan["location"] = None

    if "time" not in plan:
        plan["time"] = "current"

    if "tools" not in plan:
        plan["tools"] = []

    if "reasoning" not in plan:
        plan["reasoning"] = ""

    # --------------------------------------------------------
    # Make sure only real tools are returned
    # --------------------------------------------------------

    plan["tools"] = [
        tool
        for tool in plan["tools"]
        if tool in AVAILABLE_TOOLS
    ]

    # --------------------------------------------------------
    # Location should always be resolved first
    # --------------------------------------------------------

    if plan["location"] is not None:

        if "get_location" not in plan["tools"]:
            plan["tools"].insert(0, "get_location")

    return plan


# ============================================================
# DISPLAY PLAN
# ============================================================

def describe_plan(plan):

    print("\n================================")
    print("        LLM AGENT PLAN")
    print("================================")

    print("Intent   :", plan.get("intent"))
    print("Location :", plan.get("location"))
    print("Time     :", plan.get("time"))

    print("\nTools selected:")

    for index, tool in enumerate(
        plan.get("tools", []),
        start=1
    ):

        description = AVAILABLE_TOOLS.get(
            tool,
            "Unknown tool"
        )

        print(f"{index}. {tool}")
        print(f"   → {description}")

    print("\nPlanner reasoning:")
    print(plan.get("reasoning"))


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n================================")
    print("      SAPTHA SAGARA")
    print("       LLM PLANNER")
    print("================================")

    query = input(
        "\nAsk the Marine Agent: "
    )

    try:

        plan = create_plan(query)

        if "error" in plan:

            print("\nPlanner Error:")
            print(plan)

        else:

            describe_plan(plan)

    except Exception as e:

        print("\n================================")
        print("          PLANNER ERROR")
        print("================================")

        print(e)