import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
import searoute as sr
from dotenv import load_dotenv

from pfz import get_pfz_advisory, get_pfz_along_route, get_chlorophyll  # type: ignore
from gis import check_geofence  # type: ignore
from decision_engine import generate_fishing_advisory  # type: ignore
from evidence_agent import create_evidence, build_evidence_report  # type: ignore
from route_engine import check_route_risk, calculate_route_segments  # type: ignore

try:
    from google import genai
except ImportError:
    genai = None


# ============================================================
# SAPTHA SAGARA — Marine Intelligence Agent
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / "backend" / ".env"
ROOT_ENV_FILE = ROOT_DIR / ".env"

load_dotenv(ENV_FILE)
load_dotenv(ROOT_ENV_FILE)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = None

if not GEMINI_API_KEY:
    print("Gemini unavailable: GEMINI_API_KEY was not found.")
elif genai is None:
    print("Gemini unavailable: install google-genai.")
else:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Gemini client initialized. Configured model: {MODEL_NAME}")
    except Exception as exc:
        print(f"Gemini initialization failed: {type(exc).__name__}: {exc}")


HEADERS = {
    "User-Agent": "SAPTHA-SAGARA-Marine-Intelligence/1.0"
}

COASTAL_HARBOURS = {
    # Gujarat & Daman/Diu
    "kandla": {"name": "Deendayal (Kandla) Port, Gujarat", "latitude": 23.0020, "longitude": 70.2180},
    "deendayal": {"name": "Deendayal (Kandla) Port, Gujarat", "latitude": 23.0020, "longitude": 70.2180},
    "mundra": {"name": "Mundra Port, Gujarat", "latitude": 22.7380, "longitude": 69.7080},
    "mandvi": {"name": "Mandvi Port, Gujarat", "latitude": 22.8250, "longitude": 69.3490},
    "okha": {"name": "Okha Fishing Harbour, Gujarat", "latitude": 22.4690, "longitude": 69.0720},
    "dwarka": {"name": "Rupen / Dwarka Landing Centre, Gujarat", "latitude": 22.2440, "longitude": 68.9580},
    "porbandar": {"name": "Porbandar Fishing Harbour, Gujarat", "latitude": 21.6400, "longitude": 69.5960},
    "mangrol": {"name": "Mangrol Fishing Harbour, Gujarat", "latitude": 21.1140, "longitude": 70.1080},
    "veraval": {"name": "Veraval Fishing Harbour, Gujarat", "latitude": 20.9010, "longitude": 70.3710},
    "diu": {"name": "Vanakbara / Diu Harbour, DNHDD", "latitude": 20.7150, "longitude": 70.8750},
    "jafrabad": {"name": "Jafrabad Fishing Harbour, Gujarat", "latitude": 20.8650, "longitude": 71.3690},
    "pipavav": {"name": "Pipavav Port, Gujarat", "latitude": 20.9160, "longitude": 71.5050},
    "bhavnagar": {"name": "Bhavnagar Port, Gujarat", "latitude": 21.7580, "longitude": 72.2380},
    "surat": {"name": "Hazira / Dumas Port, Surat, Gujarat", "latitude": 21.0920, "longitude": 72.6250},
    "hazira": {"name": "Hazira Port, Gujarat", "latitude": 21.0920, "longitude": 72.6250},
    "daman": {"name": "Daman Coastal Harbour", "latitude": 20.4140, "longitude": 72.8320},

    # Maharashtra
    "dahanu": {"name": "Dahanu / Vadhavan Fishing Harbour, Maharashtra", "latitude": 19.9680, "longitude": 72.7150},
    "satpati": {"name": "Satpati Fishing Harbour, Palghar, Maharashtra", "latitude": 19.7220, "longitude": 72.6980},
    "vasai": {"name": "Vasai / Arnala Fishing Harbour, Maharashtra", "latitude": 19.3350, "longitude": 72.7850},
    "versova": {"name": "Versova Fishing Village, Mumbai", "latitude": 19.1410, "longitude": 72.7980},
    "mumbai": {"name": "Sassoon Dock / New Ferry Wharf, Mumbai", "latitude": 18.9120, "longitude": 72.8260},
    "sassoon": {"name": "Sassoon Dock, Mumbai, Maharashtra", "latitude": 18.9120, "longitude": 72.8260},
    "jnpt": {"name": "Jawaharlal Nehru Port (JNPT), Navi Mumbai", "latitude": 18.9490, "longitude": 72.9510},
    "alibag": {"name": "Alibag / Rewas Coastal Port, Maharashtra", "latitude": 18.6410, "longitude": 72.8680},
    "murud": {"name": "Agardanda / Murud-Janjira Port, Maharashtra", "latitude": 18.3010, "longitude": 72.9560},
    "harne": {"name": "Harnai (Harne) Fishing Harbour, Dapoli", "latitude": 17.8120, "longitude": 73.0890},
    "dabhol": {"name": "Dabhol Port, Maharashtra", "latitude": 17.5840, "longitude": 73.1720},
    "jaigad": {"name": "Jaigad Port, Maharashtra", "latitude": 17.3020, "longitude": 73.2120},
    "ratnagiri": {"name": "Mirkarwada Fishing Harbour, Ratnagiri", "latitude": 17.0010, "longitude": 73.2780},
    "devgad": {"name": "Devgad Fishing Harbour, Sindhudurg", "latitude": 16.3790, "longitude": 73.3710},
    "malvan": {"name": "Malvan Coastal Jetty, Maharashtra", "latitude": 16.0590, "longitude": 73.4580},
    "vengurla": {"name": "Vengurla Port, Maharashtra", "latitude": 15.8510, "longitude": 73.6180},

    # Goa
    "chapora": {"name": "Chapora Fishing Jetty, North Goa", "latitude": 15.6060, "longitude": 73.7360},
    "panaji": {"name": "Malim / Panaji Fishing Harbour, Goa", "latitude": 15.4989, "longitude": 73.8180},
    "malim": {"name": "Malim Fishing Harbour, Panaji, Goa", "latitude": 15.5040, "longitude": 73.8310},
    "goa": {"name": "Mormugao / Vasco Fishing Harbour, Goa", "latitude": 15.4089, "longitude": 73.7939},
    "mormugao": {"name": "Mormugao Port, Goa", "latitude": 15.4089, "longitude": 73.7939},
    "vasco": {"name": "Khariwada / Vasco Fishing Harbour, Goa", "latitude": 15.3980, "longitude": 73.8020},
    "cutbona": {"name": "Cutbona Fishing Jetty, South Goa", "latitude": 15.1610, "longitude": 73.9480},

    # Karnataka
    "karwar": {"name": "Karwar Baithkol Fishing Harbour, Karnataka", "latitude": 14.8050, "longitude": 74.1140},
    "belekeri": {"name": "Belekeri Port, Ankola, Karnataka", "latitude": 14.7060, "longitude": 74.2620},
    "ankola": {"name": "Belekeri / Ankola Coastal Hub, Karnataka", "latitude": 14.7060, "longitude": 74.2620},
    "tadri": {"name": "Tadri Fishing Harbour, Gokarna/Kumta", "latitude": 14.5180, "longitude": 74.3540},
    "gokarna": {"name": "Tadri / Gokarna Coastal Landing, Karnataka", "latitude": 14.5180, "longitude": 74.3540},
    "kumta": {"name": "Kumta / Tadri Fishing Harbour, Karnataka", "latitude": 14.5180, "longitude": 74.3540},
    "honnavar": {"name": "Honnavar / Kasarkod Fishing Harbour, Karnataka", "latitude": 14.2720, "longitude": 74.4260},
    "murudeshwar": {"name": "Murudeshwar Coastal Bay, Karnataka", "latitude": 14.0940, "longitude": 74.4820},
    "bhatkal": {"name": "Bhatkal Fishing Harbour, Karnataka", "latitude": 13.9680, "longitude": 74.5250},
    "byndoor": {"name": "Byndoor / Maravanthe Coastal Hub, Karnataka", "latitude": 13.8650, "longitude": 74.6080},
    "gangolli": {"name": "Gangolli Fishing Harbour, Kundapura", "latitude": 13.6350, "longitude": 74.6620},
    "kundapura": {"name": "Gangolli / Kundapura Harbour, Karnataka", "latitude": 13.6350, "longitude": 74.6620},
    "malpe": {"name": "Malpe Fishing Harbour, Udupi, Karnataka", "latitude": 13.3480, "longitude": 74.6960},
    "udupi": {"name": "Malpe Fishing Harbour, Udupi, Karnataka", "latitude": 13.3480, "longitude": 74.6960},
    "padubidri": {"name": "Hejamady / Padubidri Fishing Harbour, Karnataka", "latitude": 13.1020, "longitude": 74.7720},
    "surathkal": {"name": "New Mangalore (Panambur) Port, Surathkal", "latitude": 12.9270, "longitude": 74.8040},
    "mangalore": {"name": "Mangaluru Old Port (Bunder) Fishing Harbour", "latitude": 12.8530, "longitude": 74.8315},
    "mangaluru": {"name": "Mangaluru Old Port (Bunder) Fishing Harbour", "latitude": 12.8530, "longitude": 74.8315},
    "ullal": {"name": "Ullal Coastal Landing, Mangaluru", "latitude": 12.8050, "longitude": 74.8450},

    # Kerala
    "kasaragod": {"name": "Kasaragod / Cheruvathur Fishing Harbour, Kerala", "latitude": 12.4880, "longitude": 74.9780},
    "cheruvathur": {"name": "Cheruvathur Fishing Harbour, Kasaragod", "latitude": 12.2120, "longitude": 75.1250},
    "payyanur": {"name": "Ezhimala / Payyanur Coastal Hub, Kerala", "latitude": 12.0180, "longitude": 75.2050},
    "azhikode": {"name": "Azhikode / Azheekkal Port, Kannur", "latitude": 11.9150, "longitude": 75.3120},
    "kannur": {"name": "Mopla Bay Fishing Harbour, Kannur, Kerala", "latitude": 11.8550, "longitude": 75.3740},
    "thalassery": {"name": "Thalassery Fishing Landing, Kerala", "latitude": 11.7480, "longitude": 75.4890},
    "mahe": {"name": "Mahe Fishing Harbour, Puducherry UT", "latitude": 11.7010, "longitude": 75.5310},
    "vadakara": {"name": "Chombala / Vadakara Fishing Harbour, Kerala", "latitude": 11.6520, "longitude": 75.5540},
    "koyilandy": {"name": "Koyilandy Fishing Harbour, Kozhikode", "latitude": 11.4390, "longitude": 75.6890},
    "kozhikode": {"name": "Beypore / Puthiyappa Fishing Harbour, Kozhikode", "latitude": 11.1660, "longitude": 75.8020},
    "calicut": {"name": "Beypore Fishing Harbour, Kozhikode, Kerala", "latitude": 11.1660, "longitude": 75.8020},
    "beypore": {"name": "Beypore Port, Kozhikode, Kerala", "latitude": 11.1660, "longitude": 75.8020},
    "ponnani": {"name": "Ponnani Fishing Harbour, Malappuram, Kerala", "latitude": 10.7850, "longitude": 75.9150},
    "chavakkad": {"name": "Chettuva / Munakkakadavu Harbour, Thrissur", "latitude": 10.5310, "longitude": 76.0420},
    "thrissur": {"name": "Chettuva Coastal Harbour, Thrissur, Kerala", "latitude": 10.5310, "longitude": 76.0420},
    "munambam": {"name": "Munambam Fishing Harbour, Ernakulam, Kerala", "latitude": 10.1780, "longitude": 76.1680},
    "vypin": {"name": "Murikkumpadam / Vypin Harbour, Kochi", "latitude": 9.9920, "longitude": 76.2280},
    "kochi": {"name": "Thoppumpady (Cochin) Fishing Harbour, Kerala", "latitude": 9.9360, "longitude": 76.2580},
    "cochin": {"name": "Thoppumpady (Cochin) Fishing Harbour, Kerala", "latitude": 9.9360, "longitude": 76.2580},
    "chellanam": {"name": "Chellanam Fishing Harbour, Kochi, Kerala", "latitude": 9.7980, "longitude": 76.2760},
    "alappuzha": {"name": "Thottappally / Alappuzha Fishing Harbour, Kerala", "latitude": 9.4920, "longitude": 76.3180},
    "alleppey": {"name": "Alappuzha Coastal Port, Kerala", "latitude": 9.4920, "longitude": 76.3180},
    "kayamkulam": {"name": "Kayamkulam Fishing Harbour, Kerala", "latitude": 9.1380, "longitude": 76.4620},
    "neendakara": {"name": "Neendakara Fishing Harbour, Kollam, Kerala", "latitude": 8.9380, "longitude": 76.5390},
    "kollam": {"name": "Thangassery / Sakthikulangara Port, Kollam", "latitude": 8.8785, "longitude": 76.5560},
    "varkala": {"name": "Muthalapozhi / Varkala Harbour, Kerala", "latitude": 8.6340, "longitude": 76.7820},
    "thiruvananthapuram": {"name": "Vizhinjam International Seaport & Harbour, Kerala", "latitude": 8.3780, "longitude": 76.9880},
    "trivandrum": {"name": "Vizhinjam Fishing Harbour, Thiruvananthapuram", "latitude": 8.3780, "longitude": 76.9880},
    "vizhinjam": {"name": "Vizhinjam Fishing Harbour, Kerala", "latitude": 8.3780, "longitude": 76.9880},

    # Tamil Nadu & Puducherry
    "thengaipattinam": {"name": "Thengaipattinam Fishing Harbour, Kanyakumari", "latitude": 8.2380, "longitude": 77.1680},
    "colachel": {"name": "Colachel Fishing Harbour, Tamil Nadu", "latitude": 8.1720, "longitude": 77.2520},
    "kanyakumari": {"name": "Chinnamuttom Fishing Harbour, Kanyakumari", "latitude": 8.0950, "longitude": 77.5610},
    "chinnamuttom": {"name": "Chinnamuttom Fishing Harbour, Kanyakumari", "latitude": 8.0950, "longitude": 77.5610},
    "tuticorin": {"name": "V.O. Chidambaranar / Tuticorin Fishing Harbour", "latitude": 8.7940, "longitude": 78.1610},
    "thoothukudi": {"name": "Thoothukudi (Tuticorin) Port, Tamil Nadu", "latitude": 8.7940, "longitude": 78.1610},
    "rameswaram": {"name": "Rameswaram / Mandapam Fishing Harbour, TN", "latitude": 9.2820, "longitude": 79.3150},
    "mandapam": {"name": "Mandapam Fishing Harbour, Tamil Nadu", "latitude": 9.2770, "longitude": 79.1520},
    "nagapattinam": {"name": "Nagapattinam Fishing Harbour, Tamil Nadu", "latitude": 10.7610, "longitude": 79.8490},
    "karaikal": {"name": "Karaikal Fishing Harbour, Puducherry UT", "latitude": 10.9150, "longitude": 79.8520},
    "poombuhar": {"name": "Poombuhar / Pazhayar Fishing Harbour, TN", "latitude": 11.1440, "longitude": 79.8580},
    "cuddalore": {"name": "Cuddalore Old Town Fishing Harbour, TN", "latitude": 11.7150, "longitude": 79.7740},
    "puducherry": {"name": "Puducherry (Thengaithittu) Fishing Harbour", "latitude": 11.9080, "longitude": 79.8290},
    "pondicherry": {"name": "Puducherry (Thengaithittu) Fishing Harbour", "latitude": 11.9080, "longitude": 79.8290},
    "mahabalipuram": {"name": "Mamallapuram / Kovalam Coastal Hub, TN", "latitude": 12.6210, "longitude": 80.1980},
    "chennai": {"name": "Kasimedu (Chennai) Fishing Harbour, Tamil Nadu", "latitude": 13.1280, "longitude": 80.2980},
    "kasimedu": {"name": "Kasimedu Fishing Harbour, Chennai, TN", "latitude": 13.1280, "longitude": 80.2980},
    "ennore": {"name": "Kamarajar (Ennore) Port, Chennai, TN", "latitude": 13.2620, "longitude": 80.3410},
    "pulicat": {"name": "Pulicat Coastal Landing, Tamil Nadu", "latitude": 13.4180, "longitude": 80.3260},

    # Andhra Pradesh
    "krishnapatnam": {"name": "Krishnapatnam Port, Nellore, AP", "latitude": 14.2540, "longitude": 80.1280},
    "nellore": {"name": "Krishnapatnam / Nellore Coastal Hub, AP", "latitude": 14.2540, "longitude": 80.1280},
    "ongole": {"name": "Vodarevu / Kothapatnam Landing Centre, AP", "latitude": 15.7920, "longitude": 80.3650},
    "nizampatnam": {"name": "Nizampatnam Fishing Harbour, Guntur, AP", "latitude": 15.8950, "longitude": 80.6680},
    "machilipatnam": {"name": "Gilakaladindi (Machilipatnam) Harbour, AP", "latitude": 16.1520, "longitude": 81.1890},
    "yanam": {"name": "Yanam / Bhairavapalem Harbour", "latitude": 16.7250, "longitude": 82.2980},
    "kakinada": {"name": "Kakinada Deep Water & Fishing Harbour, AP", "latitude": 16.9820, "longitude": 82.2810},
    "visakhapatnam": {"name": "Visakhapatnam Fishing Harbour, AP", "latitude": 17.6960, "longitude": 83.3010},
    "vizag": {"name": "Visakhapatnam Fishing Harbour, AP", "latitude": 17.6960, "longitude": 83.3010},
    "bheemunipatnam": {"name": "Bheemunipatnam Coastal Jetty, AP", "latitude": 17.8910, "longitude": 83.4560},
    "srikakulam": {"name": "Kalingapatnam / Bhavanapadu Harbour, AP", "latitude": 18.5620, "longitude": 84.3310},

    # Odisha & West Bengal
    "gopalpur": {"name": "Gopalpur Port, Odisha", "latitude": 19.3020, "longitude": 84.9650},
    "puri": {"name": "Pentakota / Nuagarh (Astaranga) Harbour, Puri", "latitude": 19.7980, "longitude": 85.8420},
    "paradip": {"name": "Paradip Fishing Harbour & Port, Odisha", "latitude": 20.2650, "longitude": 86.6710},
    "paradeep": {"name": "Paradip Fishing Harbour & Port, Odisha", "latitude": 20.2650, "longitude": 86.6710},
    "dhamra": {"name": "Dhamra Fishing Harbour & Port, Odisha", "latitude": 20.7920, "longitude": 86.9650},
    "balasore": {"name": "Balaramgadi / Chandipur Harbour, Balasore", "latitude": 21.4720, "longitude": 87.0540},
    "digha": {"name": "Sankarpur (Digha) Fishing Harbour, West Bengal", "latitude": 21.6350, "longitude": 87.5680},
    "haldia": {"name": "Haldia Dock / Petuaghat Harbour, West Bengal", "latitude": 21.7950, "longitude": 87.8820},
    "fraserganj": {"name": "Fraserganj / Namkhana Fishing Harbour, WB", "latitude": 21.5780, "longitude": 88.2580},
    "kakdwip": {"name": "Kakdwip / Raidighi Fishing Harbour, WB", "latitude": 21.8680, "longitude": 88.1820},
    "kolkata": {"name": "Syama Prasad Mookerjee (Diamond Harbour) Port", "latitude": 22.1890, "longitude": 88.1880},

    # Islands
    "kavaratti": {"name": "Kavaratti Port, Lakshadweep", "latitude": 10.5660, "longitude": 72.6410},
    "lakshadweep": {"name": "Kavaratti Port, Lakshadweep", "latitude": 10.5660, "longitude": 72.6410},
    "minicoy": {"name": "Minicoy Harbour, Lakshadweep", "latitude": 8.2840, "longitude": 73.0480},
    "port blair": {"name": "Junglighat / Phoenix Bay Port, Port Blair", "latitude": 11.6680, "longitude": 92.7360},
    "andaman": {"name": "Port Blair Harbour, Andaman & Nicobar", "latitude": 11.6680, "longitude": 92.7360},
}


# ============================================================
# 1. UNIVERSAL LOCATION LOOKUP & EXTRACTION
# ============================================================

def get_location(location_name):
    """
    Universal resolver for any Indian port, coastal town, city, or 'lat, lon' string.
    """
    if not location_name or not str(location_name).strip():
        return {"error": "Location name cannot be empty."}

    clean_name = str(location_name).strip()

    coord_match = re.match(
        r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$",
        clean_name,
    )
    if coord_match:
        lat_val = float(coord_match.group(1))
        lon_val = float(coord_match.group(2))
        return {
            "name": f"Selected Point ({lat_val:.4f}, {lon_val:.4f})",
            "latitude": lat_val,
            "longitude": lon_val,
            "coordinates": [lat_val, lon_val],
        }

    lookup_key = clean_name.lower().split(",")[0].strip()
    if lookup_key in COASTAL_HARBOURS:
        hub = COASTAL_HARBOURS[lookup_key]
        return {
            "name": hub["name"],
            "latitude": hub["latitude"],
            "longitude": hub["longitude"],
            "coordinates": [hub["latitude"], hub["longitude"]],
        }

    for key, hub in COASTAL_HARBOURS.items():
        if key in lookup_key or lookup_key in key:
            return {
                "name": hub["name"],
                "latitude": hub["latitude"],
                "longitude": hub["longitude"],
                "coordinates": [hub["latitude"], hub["longitude"]],
            }

    try:
        geo_resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": lookup_key,
                "count": 5,
                "language": "en",
                "format": "json",
            },
            headers=HEADERS,
            timeout=10,
        )
        geo_resp.raise_for_status()
        geo_results = geo_resp.json().get("results", [])

        india_matches = [
            r for r in geo_results if str(r.get("country_code", "")).upper() == "IN"
        ]
        chosen = india_matches[0] if india_matches else (geo_results[0] if geo_results else None)

        if chosen:
            lat_val = float(chosen["latitude"])
            lon_val = float(chosen["longitude"])
            admin = chosen.get("admin1", "")
            disp = f"{chosen.get('name', clean_name)}, {admin}, India".replace(", ,", ",")
            return {
                "name": disp,
                "latitude": lat_val,
                "longitude": lon_val,
                "coordinates": [lat_val, lon_val],
            }
    except Exception as exc:
        print(f"Open-Meteo geocoding fallback to Nominatim: {exc}")

    search_name = (
        clean_name if "india" in clean_name.lower() else f"{clean_name}, India"
    )
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": search_name,
                "format": "json",
                "limit": 1,
                "countrycodes": "in",
            },
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        results = response.json()

        if results:
            place = results[0]
            latitude = float(place["lat"])
            longitude = float(place["lon"])
            return {
                "name": place.get("display_name", clean_name),
                "latitude": latitude,
                "longitude": longitude,
                "coordinates": [latitude, longitude],
            }
    except Exception as exc:
        print(f"Nominatim lookup failed: {exc}")

    return {"error": f"Could not find location: {clean_name}"}


def is_current_route_query(query):
    """Detect if the user is asking about their currently active route."""
    q_low = query.lower()
    return bool(
        re.search(
            r"\b(current route|my route|this route|along the route|route conditions|selected route|our route)\b",
            q_low,
        )
    )


def extract_explicit_route_request(query):
    """
    ONLY return (origin, destination) if the user explicitly asks to plan, make,
    or find a new route between two places (e.g., 'plan a route from Kochi to Goa').
    """
    q_low = query.lower()
    route_intent = re.search(
        r"\b(route|plan|navigate|sail|travel|voyage|path|course)\b",
        q_low,
    )
    if not route_intent:
        return None, None

    match = re.search(
        r"\b(?:from|between)\s+([a-zA-Z]+)\s+(?:to|and)\s+([a-zA-Z]+)\b",
        query,
        re.IGNORECASE,
    )
    if match:
        orig_cand = match.group(1).strip()
        dest_cand = match.group(2).strip()
        stop_words = {"wind", "wave", "waves", "weather", "current", "my", "this", "the", "sea"}
        if orig_cand.lower() not in stop_words and dest_cand.lower() not in stop_words:
            return orig_cand.title(), dest_cand.title()
    return None, None


def extract_explicit_location(query):
    """
    Extract a location from the user's query ONLY if one was actually mentioned.
    """
    query_lower = query.lower()

    aliases = sorted(COASTAL_HARBOURS.keys(), key=len, reverse=True)
    for alias in aliases:
        if re.search(r"\b" + re.escape(alias) + r"\b", query_lower):
            return alias.title()

    match = re.search(
        r"\b(?:near|at|around|off|in|coast of|coastal waters near)"
        r"\s+([a-zA-Z][a-zA-Z\s-]{1,30})",
        query,
        re.IGNORECASE,
    )

    if match:
        candidate = match.group(1).strip()
        candidate = re.split(
            r"\b(?:for|with|including|and|today|tomorrow|right now|currently|route|my|current)\b|[?,!.]",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        stop_phrases = {"my", "the", "current", "this", "route", "our", "sea", "ocean"}
        if candidate and candidate.lower() not in stop_phrases:
            return candidate.title()

    return None


# ============================================================
# 2. FETCH WEATHER & MARINE CONDITIONS
# ============================================================

def get_weather(latitude, longitude):
    """Fetch current weather fields from Open-Meteo."""
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
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()
        current = result.get("current", {})

        return {
            "available": bool(current),
            "source": "Open-Meteo",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "current": current,
            "units": result.get("current_units", {}),
        }
    except (requests.RequestException, ValueError) as exc:
        print(f"Weather retrieval failed: {exc}")
        return {
            "available": False,
            "source": "Open-Meteo",
            "error": str(exc),
        }


def get_marine_conditions(latitude, longitude):
    """Fetch available wave, swell, and SST fields from Open-Meteo Marine API."""
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "wave_height,wave_direction,wave_period,"
            "swell_wave_height,swell_wave_direction,swell_wave_period,"
            "sea_surface_temperature"
        ),
        "timezone": "UTC",
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()
        current = result.get("current", {})

        return {
            "available": bool(current),
            "source": "Open-Meteo Marine API",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "current": current,
            "units": result.get("current_units", {}),
        }
    except (requests.RequestException, ValueError) as exc:
        print(f"Marine data retrieval failed: {exc}")
        return {
            "available": False,
            "source": "Open-Meteo Marine API",
            "error": str(exc),
        }


# ============================================================
# 3. PAN-INDIA COASTAL & CROSS-COAST ROUTE PLANNING ENGINE
# ============================================================

def calculate_distance(origin, destination):
    """Calculate great-circle distance between (lat, lon) coordinates in km."""
    lat1 = math.radians(origin[0])
    lon1 = math.radians(origin[1])
    lat2 = math.radians(destination[0])
    lon2 = math.radians(destination[1])

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    a = min(1.0, max(0.0, a))
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Ordered South -> North along the Arabian Sea (West Coast)
WEST_COAST_CORRIDOR = [
    (8.02, 77.38),   # Off Kanyakumari
    (8.35, 76.82),   # Off Vizhinjam
    (8.86, 76.42),   # Off Kollam
    (9.48, 76.18),   # Off Alappuzha
    (9.96, 76.08),   # Off Kochi
    (10.78, 75.78),  # Off Ponnani
    (11.15, 75.62),  # Off Kozhikode
    (11.85, 75.18),  # Off Kannur
    (12.48, 74.82),  # Off Kasaragod
    (12.85, 74.68),  # Off Mangaluru
    (13.35, 74.55),  # Off Udupi / Malpe
    (13.96, 74.38),  # Off Bhatkal
    (14.52, 74.20),  # Off Kumta / Tadri
    (14.80, 73.98),  # Off Karwar
    (15.40, 73.68),  # Off Goa / Mormugao
    (16.38, 73.22),  # Off Devgad
    (16.98, 73.12),  # Off Ratnagiri
    (18.90, 72.68),  # Off Mumbai
    (20.85, 70.20),  # Off Veraval
    (22.45, 68.90),  # Off Okha
]


# Ordered West -> East around the Southern & Eastern Sri Lanka deep-water lane
SOUTHERN_PENINSULA_CORRIDOR = [
    (7.65, 77.50),   # Wadge Bank (South of Kanyakumari)
    (6.65, 79.15),   # Southwest of Colombo
    (5.65, 80.55),   # South of Dondra Head / Galle
    (5.95, 81.80),   # Southeast of Great Basses Reef (clears Yala coast)
    (6.95, 82.25),   # East of Sangamankanda Point (clears Ampara coast)
    (8.35, 81.85),   # East of Trincomalee
    (9.65, 80.85),   # Northeast of Jaffna / Point Pedro
]

# Ordered South -> North along the Bay of Bengal (East Coast)
EAST_COAST_CORRIDOR = [
    (8.02, 77.65),   # Off Kanyakumari East
    (8.78, 78.35),   # Off Tuticorin
    (9.28, 79.45),   # Off Rameswaram / Palk Bay
    (10.76, 80.02),  # Off Nagapattinam
    (11.90, 79.98),  # Off Puducherry
    (13.12, 80.45),  # Off Chennai
    (14.25, 80.28),  # Off Krishnapatnam
    (15.90, 81.15),  # Off Machilipatnam
    (16.98, 82.45),  # Off Kakinada
    (17.69, 83.48),  # Off Visakhapatnam
    (19.30, 85.10),  # Off Gopalpur
    (20.26, 86.82),  # Off Paradip
    (21.55, 87.85),  # Off Digha / Haldia
]


def _is_west_coast(pt):
    return 7.8 <= pt[0] <= 23.5 and 68.0 <= pt[1] <= 77.6


def _is_east_coast(pt):
    return 7.8 <= pt[0] <= 22.5 and 77.6 < pt[1] <= 89.0


def _densify_segments(points, min_waypoints=6):
    if len(points) >= min_waypoints:
        return points

    densified = []
    steps_per_seg = max(2, math.ceil(min_waypoints / max(1, len(points) - 1)))
    for i in range(len(points) - 1):
        lat1, lon1 = points[i]
        lat2, lon2 = points[i + 1]
        for step in range(steps_per_seg):
            frac = step / steps_per_seg
            densified.append((
                round(lat1 + (lat2 - lat1) * frac, 5),
                round(lon1 + (lon2 - lon1) * frac, 5),
            ))
    densified.append(points[-1])
    return densified


def _remove_hairpin_detours(points):
    """
    Remove backward V-hook snapping artifacts (e.g., where searoute snaps a port
    north to Mangalore before sailing south, or snaps past the destination).
    """
    if len(points) <= 2:
        return points

    cleaned = list(points)
    changed = True

    while changed and len(cleaned) >= 3:
        changed = False
        i = 0
        while i < len(cleaned) - 2:
            p1, p2, p3 = cleaned[i], cleaned[i + 1], cleaned[i + 2]
            v1_lat, v1_lon = p2[0] - p1[0], p2[1] - p1[1]
            v2_lat, v2_lon = p3[0] - p2[0], p3[1] - p2[1]
            mag1 = math.hypot(v1_lat, v1_lon)
            mag2 = math.hypot(v2_lat, v2_lon)

            if mag1 > 0 and mag2 > 0:
                cos_angle = (v1_lat * v2_lat + v1_lon * v2_lon) / (mag1 * mag2)
                # If the route makes a sharp reversal (cos_angle < -0.35 means >110° turn back)
                if cos_angle < -0.35:
                    cleaned.pop(i + 1)
                    changed = True
                    break
            i += 1

    return cleaned


def _build_corridor_route(start, end, corridor, is_west=True):
    going_north = end[0] >= start[0]
    min_lat = min(start[0], end[0])
    max_lat = max(start[0], end[0])

    if abs(start[0] - end[0]) < 0.25:
        return _densify_segments([start, end], min_waypoints=5)

    lon_shift = -0.08 if is_west else 0.08
    start_offshore = (start[0], start[1] + lon_shift)
    end_offshore = (end[0], end[1] + lon_shift)

    corridor_nodes = [
        node
        for node in corridor
        if (min_lat + 0.12) < node[0] < (max_lat - 0.12)
    ]

    if not going_north:
        corridor_nodes.reverse()

    raw_path = [start, start_offshore] + corridor_nodes + [end_offshore, end]

    cleaned = [raw_path[0]]
    for pt in raw_path[1:]:
        if calculate_distance(cleaned[-1], pt) > 2.5:
            cleaned.append(pt)
    if cleaned[-1] != end:
        cleaned.append(end)

    return _densify_segments(_remove_hairpin_detours(cleaned), min_waypoints=6)


def _build_cross_coast_route(start, end, west_to_east=True):
    """
    Build a continuous sea route between India's West Coast and East Coast
    that clears Sri Lanka's southern and eastern coastline cleanly.
    """
    if west_to_east:
        west_pt, east_pt = start, end
    else:
        east_pt, west_pt = start, end

    west_offshore = (west_pt[0], min(west_pt[1] - 0.10, west_pt[1]))
    east_offshore = (east_pt[0], max(east_pt[1] + 0.10, east_pt[1]))

    # Sail south along the West Coast from west_pt down to Kanyakumari
    west_leg = [
        node for node in reversed(WEST_COAST_CORRIDOR)
        if node[0] < (west_pt[0] - 0.15)
    ]

    # If the East Coast point is inside the Gulf of Mannar (e.g., Tuticorin),
    # round Kanyakumari directly without going around Sri Lanka
    if east_pt[0] < 9.35 and east_pt[1] < 79.50:
        peninsula_leg = [(7.65, 77.50), (8.25, 78.30)]
        east_leg = []
    else:
        peninsula_leg = list(SOUTHERN_PENINSULA_CORRIDOR)
        east_leg = [
            node for node in EAST_COAST_CORRIDOR
            if 10.5 <= node[0] < (east_pt[0] - 0.15)
        ]

    if west_to_east:
        raw_path = (
            [start, west_offshore]
            + west_leg
            + peninsula_leg
            + east_leg
            + [east_offshore, end]
        )
    else:
        raw_path = (
            [start, east_offshore]
            + list(reversed(east_leg))
            + list(reversed(peninsula_leg))
            + list(reversed(west_leg))
            + [west_offshore, end]
        )

    cleaned = [raw_path[0]]
    for pt in raw_path[1:]:
        if calculate_distance(cleaned[-1], pt) > 3.0:
            cleaned.append(pt)
    if cleaned[-1] != end:
        cleaned.append(end)

    return _remove_hairpin_detours(cleaned)


def run_route_planning(origin, destination):
    """Return a sea route along with live SST + Chlorophyll-a PFZ sectors."""
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
            "error": f"Destination lookup failed: {destination_location['error']}",
        }

    start = (origin_location["latitude"], origin_location["longitude"])
    end = (destination_location["latitude"], destination_location["longitude"])
    straight_distance_km = calculate_distance(start, end)

    try:
        if _is_west_coast(start) and _is_west_coast(end):
            route_coords = _build_corridor_route(
                start, end, WEST_COAST_CORRIDOR, is_west=True
            )
            route_method = "Arabian Sea Coastal Corridor"
        elif _is_east_coast(start) and _is_east_coast(end):
            route_coords = _build_corridor_route(
                start, end, EAST_COAST_CORRIDOR, is_west=False
            )
            route_method = "Bay of Bengal Coastal Corridor"
        elif _is_west_coast(start) and _is_east_coast(end):
            route_coords = _build_cross_coast_route(
                start, end, west_to_east=True
            )
            route_method = "Peninsular West-to-East Maritime Corridor"
        elif _is_east_coast(start) and _is_west_coast(end):
            route_coords = _build_cross_coast_route(
                start, end, west_to_east=False
            )
            route_method = "Peninsular East-to-West Maritime Corridor"
        else:
            sea_route = sr.searoute(
                [start[1], start[0]],
                [end[1], end[0]],
                append_orig_dest=True,
            )
            coordinates = sea_route["geometry"]["coordinates"]
            route_coords = [
                (float(coord[1]), float(coord[0])) for coord in coordinates
            ]
            route_coords = _remove_hairpin_detours(route_coords)
            route_coords = _densify_segments(route_coords, min_waypoints=6)
            route_method = "Searoute Maritime Network"

        waypoints = []
        restricted_hits = []
        cumulative_km = 0.0

        for idx, (lat, lon) in enumerate(route_coords):
            if idx > 0:
                cumulative_km += calculate_distance(route_coords[idx - 1], (lat, lon))

            geo_check = check_geofence(lat, lon)
            is_restricted = geo_check.get("restricted", False)
            if is_restricted:
                restricted_hits.append({
                    "sequence": idx + 1,
                    "zone": geo_check.get("zone"),
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                })

            waypoints.append({
                "sequence": idx + 1,
                "latitude": round(lat, 5),
                "longitude": round(lon, 5),
                "cumulative_km": round(cumulative_km, 2),
                "restricted": is_restricted,
                "zone_name": geo_check.get("zone"),
            })

        route_distance_km = cumulative_km if cumulative_km > 0 else straight_distance_km

        # Fetch all live PFZs (Coastal + Deep-Sea EEZ) and tag the ones along this route
        route_pfz = get_pfz_along_route(route_coords, corridor_radius_km=95)

        mid_idx = len(route_coords) // 2
        mid_lat, mid_lon = route_coords[mid_idx]
        mid_weather = get_weather(mid_lat, mid_lon)
        mid_marine = get_marine_conditions(mid_lat, mid_lon)
        mid_gis = check_geofence(mid_lat, mid_lon)

        weather_for_engine = {
            "current": {
                "wind_speed": mid_weather.get("current", {}).get("wind_speed_10m"),
                "precipitation": mid_weather.get("current", {}).get("precipitation"),
            }
        }
        ocean_for_engine = {
            "current": {
                "wave_height": mid_marine.get("current", {}).get("wave_height"),
            }
        }
        fishing_advisory = generate_fishing_advisory(
            weather=weather_for_engine,
            ocean=ocean_for_engine,
            pfz=route_pfz,
            gis={"restricted": bool(restricted_hits) or mid_gis.get("restricted", False)},
        )

        risk_summary = check_route_risk(fishing_advisory["risk_score"])
        estimated_hours = round(route_distance_km / 22.22, 1)
        nautical_miles = round(route_distance_km * 0.539957, 2)

    except Exception as exc:
        print(f"Sea-route generation failed: {type(exc).__name__}: {exc}")
        return {
            "success": False,
            "error": "Unable to generate the sea-route estimate. Check backend logs.",
        }

    return {
        "success": True,
        "origin": origin_location,
        "destination": destination_location,
        "straight_line_distance_km": round(straight_distance_km, 2),
        "route_distance_km": round(route_distance_km, 2),
        "route_distance_nm": nautical_miles,
        "estimated_duration_hours": estimated_hours,
        "waypoints": waypoints,
        "segments": calculate_route_segments(route_coords),
        "pfz": route_pfz,
        "weather": mid_weather,
        "marine_conditions": mid_marine,
        "fishing_advisory": fishing_advisory,
        "route_risk": risk_summary,
        "restricted_zones_crossed": restricted_hits,
        "route_type": f"{route_method} ({risk_summary['risk_level']} RISK)",
        "limitations": [
            "This is a route visualization estimate, not a certified navigational route.",
            "The route has not been verified against official nautical charts or current coastline data.",
            "Bathymetry, vessel draft, shipping restrictions, currents, and official warnings must be checked independently.",
        ],
    }


# ============================================================
# 4. STRUCTURED REPORT GENERATION (GEMINI + FALLBACK)
# ============================================================

def generate_fallback_report(query, location, weather, marine, pfz, advisory, gis, chlorophyll=None, active_route=None):
    location_name = location.get("name", "Requested location")
    weather_data = weather.get("current", {})
    marine_data = marine.get("current", {})
    weather_units = weather.get("units", {})
    marine_units = marine.get("units", {})

    def measurement(data, units, key, label):
        value = data.get(key)
        if value is None:
            return None
        unit = units.get(key, "") if isinstance(units, dict) else ""
        suffix = f" {unit}" if unit else ""
        return f"**{label}:** {value}{suffix}"

    lines = ["### Weather & Ocean Conditions"]
    if active_route and active_route.get("success"):
        lines.append(
            f"- **Active Route Analyzed:** {active_route['origin']['name']} → {active_route['destination']['name']} "
            f"({active_route['route_distance_km']} km / {active_route['route_distance_nm']} NM)"
        )
    else:
        lines.append(
            f"- **Location:** {location_name} ({location.get('latitude')}, {location.get('longitude')})"
        )

    observation_time = weather_data.get("time")
    if observation_time:
        lines.append(f"- **Observation Time (UTC):** {observation_time}")

    weather_items = [
        measurement(weather_data, weather_units, "temperature_2m", "Air Temperature"),
        measurement(marine_data, marine_units, "sea_surface_temperature", "Sea Surface Temp (SST)"),
        measurement(weather_data, weather_units, "wind_speed_10m", "Wind Speed"),
        measurement(weather_data, weather_units, "wind_gusts_10m", "Wind Gusts"),
        measurement(weather_data, weather_units, "wind_direction_10m", "Wind Direction"),
        measurement(weather_data, weather_units, "precipitation", "Precipitation"),
        measurement(marine_data, marine_units, "wave_height", "Significant Wave Height"),
        measurement(marine_data, marine_units, "wave_period", "Wave Period"),
        measurement(marine_data, marine_units, "swell_wave_height", "Swell Height"),
    ]
    lines.extend(f"- {item}" for item in weather_items if item)

    if chlorophyll and chlorophyll.get("chlorophyll_mg_m3") is not None:
        lines.append(
            f"- **Chlorophyll-a Concentration:** {chlorophyll['chlorophyll_mg_m3']} mg/m³ ({chlorophyll.get('bloom_status')})"
        )

    lines.extend([
        "",
        "### Fishing Risk Assessment",
        f"- **Risk Status:** **{advisory.get('status', 'CAUTION')}** "
        f"(Risk Level: **{advisory.get('risk_level', 'MODERATE')}** · Score: **{advisory.get('risk_score', 0)}/100**)",
        f"- **Geofence Check:** {'Inside restricted zone (' + str(gis.get('zone')) + ')' if gis.get('restricted') else 'Outside known restricted marine zones'}",
        f"- **Assessment Summary:** {advisory.get('recommendation', '')}",
    ])

    zones = pfz.get("zones", [])
    all_zones = pfz.get("all_zones", zones)
    lines.extend([
        "",
        f"### Potential Fishing Zones ({len(zones)} Corridor / {len(all_zones)} Total Live Sectors)",
    ])
    if zones:
        for z in zones[:4]:
            sst_str = f" | SST: {z['sst_c']}°C" if z.get("sst_c") is not None else ""
            chl_str = f" | Chl-a: {z['chlorophyll_mg_m3']} mg/m³" if z.get("chlorophyll_mg_m3") is not None else ""
            lines.append(
                f"- **{z['zone_id']} ({z['sector']}):** {z.get('distance_km', '—')} km {z.get('bearing', '')} "
                f"| Depth: {z.get('depth_m')} m{sst_str}{chl_str} | Species: {z.get('species', 'Pelagic shoals')}"
            )
    else:
        lines.append("- Use the PFZ layer toggle on the interactive map below to inspect all active sectors.")

    lines.extend([
        "",
        "### Operational Recommendation & Limitations",
        "- All active PFZ sectors with live SST, Chlorophyll-a, and wave metrics are available on the map below.",
        "- Verify local IMD port warnings before departure.",
    ])

    return "\n".join(lines)


def generate_summary(query, location, weather, marine, pfz, advisory, gis, chlorophyll=None, active_route=None):
    evidence_payload = {
        "user_query": query,
        "location": location,
        "active_route_summary": {
            "origin": active_route.get("origin"),
            "destination": active_route.get("destination"),
            "route_distance_km": active_route.get("route_distance_km"),
            "route_distance_nm": active_route.get("route_distance_nm"),
            "estimated_duration_hours": active_route.get("estimated_duration_hours"),
            "route_risk": active_route.get("route_risk"),
        }
        if active_route
        else None,
        "weather": weather,
        "marine_conditions": marine,
        "chlorophyll": chlorophyll,
        "pfz_corridor_zones": pfz.get("zones", [])[:5],
        "total_live_pfz_count": len(pfz.get("all_zones", [])),
        "fishing_risk_assessment": advisory,
        "gis_geofence": gis,
    }

    if client is not None:
        prompt = f"""
You are the SAPTHA SAGARA Marine Intelligence Agent.
Write a clear, structured, evidence-based marine intelligence report for fishermen and coastal operators.

EVIDENCE PAYLOAD:
{json.dumps(evidence_payload, ensure_ascii=False, default=str)}

Use Markdown with these exact four section headings (keep total length under 230 words):

### Weather & Ocean Conditions
- State the analyzed route (if `active_route_summary` is present) or resolved location name and observation time.
- Bullet the air temperature, sea surface temperature (SST), chlorophyll-a concentration (mg/m³), wind speed, wind gusts, wind direction, wave height, wave period, and swell height.

### Fishing Risk Assessment
- State the deterministic Risk Status (**{advisory.get('status')}**), Risk Level (**{advisory.get('risk_level')}**), and Score (**{advisory.get('risk_score')}/100**).
- Mention the GIS restricted-zone status and key environmental factors.

### Potential Fishing Zones (PFZ)
- List the active PFZ zones from `pfz_corridor_zones` including Zone ID, Sector, distance (km), depth (m), live SST (°C), Chlorophyll-a (mg/m³), and target fish species.

### Recommendation & Limitations
- Give 1-2 actionable safety steps and note that model-derived data do not replace official IMD/INCOIS clearance.
"""
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            report = getattr(response, "text", None)
            if report and report.strip():
                return report.strip(), "Gemini"
        except Exception as exc:
            print(f"Gemini report generation failed: {type(exc).__name__}: {exc}")

    report = generate_fallback_report(
        query, location, weather, marine, pfz, advisory, gis, chlorophyll=chlorophyll, active_route=active_route
    )
    return report, "Structured Engine"


# ============================================================
# 5. MARINE QUERY ENTRY POINT — USED BY FASTAPI
# ============================================================

def run_agent(query, current_origin=None, current_destination=None):
    """
    Fetch weather, marine, Chlorophyll-a, live PFZ, GIS, and risk assessment data.
    NEVER overwrites the user's active route unless the query explicitly asks
    to create/plan a new route between two locations!
    """
    if not isinstance(query, str) or len(query.strip()) < 2:
        return {
            "success": False,
            "error": "Please provide a valid marine query.",
        }

    query = query.strip()

    explicit_orig, explicit_dest = extract_explicit_route_request(query)
    explicit_place = None if explicit_orig else extract_explicit_location(query)

    active_route = None
    route_updated_by_query = False

    if explicit_orig and explicit_dest:
        active_route = run_route_planning(explicit_orig, explicit_dest)
        route_updated_by_query = True
        place_name = explicit_orig
    elif (
        (is_current_route_query(query) or not explicit_place)
        and current_origin
        and current_destination
    ):
        active_route = run_route_planning(current_origin, current_destination)
        route_updated_by_query = False
        place_name = current_origin
    else:
        place_name = explicit_place or current_origin or "Mangalore"

    if active_route and active_route.get("success"):
        location = {
            "name": f"{active_route['origin']['name']} → {active_route['destination']['name']}",
            "latitude": active_route["origin"]["latitude"],
            "longitude": active_route["origin"]["longitude"],
            "coordinates": [
                active_route["origin"]["latitude"],
                active_route["origin"]["longitude"],
            ],
        }
        weather = active_route["weather"]
        marine = active_route["marine_conditions"]
        pfz = active_route["pfz"]
        fishing_advisory = active_route["fishing_advisory"]
        chlorophyll = get_chlorophyll(
            active_route["origin"]["latitude"],
            active_route["origin"]["longitude"],
        )
        gis = {
            "restricted": bool(active_route.get("restricted_zones_crossed")),
            "zone": (
                active_route["restricted_zones_crossed"][0]["zone"]
                if active_route.get("restricted_zones_crossed")
                else None
            ),
        }
    else:
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
        chlorophyll = get_chlorophyll(latitude, longitude)
        pfz = get_pfz_advisory(latitude, longitude, radius_km=180)
        gis = check_geofence(latitude, longitude)

        weather_for_engine = {
            "current": {
                "wind_speed": weather.get("current", {}).get("wind_speed_10m"),
                "precipitation": weather.get("current", {}).get("precipitation"),
            }
        }
        ocean_for_engine = {
            "current": {
                "wave_height": marine.get("current", {}).get("wave_height"),
            }
        }
        fishing_advisory = generate_fishing_advisory(
            weather=weather_for_engine,
            ocean=ocean_for_engine,
            pfz=pfz,
            gis=gis,
        )

    evidence_items = [
        create_evidence("weather", weather, weather.get("source", "Open-Meteo"), weather.get("retrieved_at"), location=location["name"]),
        create_evidence("marine", marine, marine.get("source", "Open-Meteo Marine API"), marine.get("retrieved_at"), location=location["name"]),
        create_evidence("chlorophyll", chlorophyll, chlorophyll.get("source", "Biophysical Upwelling Model"), location=location["name"]),
        create_evidence("pfz", pfz, pfz.get("source", "INCOIS + Live SST/Chlorophyll Engine"), location=location["name"]),
        create_evidence("gis", gis, "SAPTHA SAGARA GIS Geofence", location=location["name"]),
    ]
    evidence_report = build_evidence_report(evidence_items)

    summary, summary_generated_by = generate_summary(
        query,
        location,
        weather,
        marine,
        pfz,
        fishing_advisory,
        gis,
        chlorophyll=chlorophyll,
        active_route=active_route,
    )

    return {
        "success": True,
        "query": query,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "location": location,
        "weather": weather,
        "marine_conditions": marine,
        "chlorophyll": chlorophyll,
        "pfz": pfz,
        "gis": gis,
        "fishing_advisory": fishing_advisory,
        "recommended_route": active_route if route_updated_by_query else None,
        "route_updated_by_query": route_updated_by_query,
        "recommended_origin": explicit_orig if route_updated_by_query else None,
        "recommended_destination": explicit_dest if route_updated_by_query else None,
        "evidence_report": evidence_report,
        "summary": summary,
        "summary_generated_by": summary_generated_by,
        "limitations": [
            "Weather, SST, and marine wave data are fetched live from Open-Meteo models.",
            "PFZ locations combine INCOIS sectors with live SST, Chlorophyll-a, and ocean current drift.",
            "Always verify official IMD alerts before departing harbour.",
        ],
    }