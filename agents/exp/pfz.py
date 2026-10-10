import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two coordinates in km."""
    earth_radius = 6371.0
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius * c

def get_pfz_advisory(latitude=None, longitude=None, radius_km=150):
    """
    Fetch INCOIS Potential Fishing Zone advisories.
    Sectors strictly follow the official 14 INCOIS divisions (SEC001-SEC014).
    """
    
    # Official INCOIS Marine Sectors
    mock_incois_database = [
        {"zone_id": "PFZ-SEC001", "lat": 21.00, "lon": 70.00, "sector": "GUJARAT", "depth_m": 45},
        {"zone_id": "PFZ-SEC002", "lat": 18.00, "lon": 72.50, "sector": "MAHARASHTRA", "depth_m": 60},
        {"zone_id": "PFZ-SEC003", "lat": 15.40, "lon": 73.50, "sector": "GOA", "depth_m": 35},
        {"zone_id": "PFZ-SEC004", "lat": 13.50, "lon": 74.20, "sector": "KARNATAKA", "depth_m": 40},
        {"zone_id": "PFZ-SEC005", "lat": 10.50, "lon": 75.80, "sector": "KERALA", "depth_m": 55},
        {"zone_id": "PFZ-SEC006", "lat": 8.50,  "lon": 78.50, "sector": "SOUTH TAMILNADU", "depth_m": 30},
        {"zone_id": "PFZ-SEC007", "lat": 12.00, "lon": 80.20, "sector": "NORTH TAMILNADU", "depth_m": 45},
        {"zone_id": "PFZ-SEC008", "lat": 14.50, "lon": 80.50, "sector": "SOUTH ANDHRA PRADESH", "depth_m": 50},
        {"zone_id": "PFZ-SEC009", "lat": 17.50, "lon": 83.50, "sector": "NORTH ANDHRA PRADESH", "depth_m": 65},
        {"zone_id": "PFZ-SEC010", "lat": 19.50, "lon": 85.50, "sector": "ODISHA", "depth_m": 40},
        {"zone_id": "PFZ-SEC011", "lat": 21.50, "lon": 88.00, "sector": "WEST BENGAL", "depth_m": 25},
        {"zone_id": "PFZ-SEC012", "lat": 11.50, "lon": 92.50, "sector": "ANDAMAN", "depth_m": 80},
        {"zone_id": "PFZ-SEC013", "lat": 8.00,  "lon": 93.50, "sector": "NICOBAR", "depth_m": 85},
        {"zone_id": "PFZ-SEC014", "lat": 10.50, "lon": 72.50, "sector": "LAKSHADWEEP", "depth_m": 120}
    ]

    available_zones = []

    # If coordinates are provided, filter by proximity to the user's requested location
    if latitude is not None and longitude is not None:
        for zone in mock_incois_database:
            dist = calculate_distance(float(latitude), float(longitude), zone["lat"], zone["lon"])
            if dist <= radius_km:
                zone_data = zone.copy()
                zone_data["distance_km"] = round(dist, 2)
                available_zones.append(zone_data)
    else:
        available_zones = mock_incois_database

    return {
        "status": "SUCCESS",
        "source": "INCOIS_PROTOTYPE",
        "zones": available_zones,
        "validity": "48_HOURS",
        "message": f"Found {len(available_zones)} active Potential Fishing Zones." if available_zones else "No active PFZs in this area."
    }

if __name__ == "__main__":
    import json
    # Testing the PFZ module near Mangalore, Karnataka
    print("Testing PFZ module near Mangalore...")
    result = get_pfz_advisory(12.9141, 74.8560)
    print(json.dumps(result, indent=2))