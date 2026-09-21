import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


BASE_URL = "https://incois.gov.in/MarineFisheries/"


def dms_to_decimal(d, m, s, direction):
    value = float(d) + float(m) / 60 + float(s) / 3600

    if direction in ["S", "W"]:
        value = -value

    return round(value, 6)


def get_pfz_advisory():

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # 1. Open main page
    url = BASE_URL + "TextDataHome?mfid=1&request_locale=en"

    response = session.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 2. Find Karnataka
    option = None

    for opt in soup.find_all("option"):
        if opt.get_text(strip=True).upper() == "KARNATAKA":
            option = opt
            break

    if not option:
        return {"error": "Karnataka not found"}

    value = option.get("value")

    secid = value.split("secid=")[1].split("&")[0]

    # 3. Get Karnataka PFZ page
    response = session.get(
        BASE_URL + "TextData",
        params={"secid": secid},
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    # 4. Extract advisory date
    date_match = re.search(
        r"LIKELY AVAILABILITY OF FISH STOCK TILL\s+(\d{2}\s+\w+\s+\d{4})",
        text
    )

    valid_until = date_match.group(1) if date_match else None

    # 5. Extract PFZ rows
    pattern = re.compile(
        r"(\w+)\s+"              # Landing center
        r"(SW|SE|NW|NE|N|S|E|W)\s+"  # Direction
        r"(\d+)\s+"              # Bearing
        r"(\d+-\d+)\s+"          # Distance
        r"(\d+-\d+)\s+"          # Depth
        r"(\d+)\s+(\d+)\s+(\d+)\s+([NS])\s+"  # Latitude
        r"(\d+)\s+(\d+)\s+(\d+)\s+([EW])"     # Longitude
    )

    zones = []

    for match in pattern.finditer(text):

        (
            landing_center,
            direction,
            bearing,
            distance,
            depth,
            lat_d,
            lat_m,
            lat_s,
            lat_dir,
            lon_d,
            lon_m,
            lon_s,
            lon_dir
        ) = match.groups()

        latitude = dms_to_decimal(
            lat_d, lat_m, lat_s, lat_dir
        )

        longitude = dms_to_decimal(
            lon_d, lon_m, lon_s, lon_dir
        )

        zones.append({
            "landing_center": landing_center,
            "direction": direction,
            "bearing": int(bearing),
            "distance_km": distance,
            "depth_m": depth,
            "latitude": latitude,
            "longitude": longitude
        })

    return {
        "source": "INCOIS",
        "sector": "KARNATAKA",
        "sector_id": secid,
        "valid_until": valid_until,
        "zones": zones
    }


if __name__ == "__main__":

    result = get_pfz_advisory()

    print("\n=== INCOIS PFZ ===")

    print("Source:", result["source"])
    print("Sector:", result["sector"])
    print("Valid Until:", result["valid_until"])

    print("\nFishing Zones:")

    for zone in result["zones"]:
        print(zone)