import requests

class OceanAgent:
    """
    Handles marine specific conditions and oceanography data.
    Designed for multi-agent maritime routing integration.
    """
    
    def __init__(self):
        self.marine_url = "https://marine-api.open-meteo.com/v1/marine"
        self.headers = {"User-Agent": "ORCA-MarineAI/1.0"}

    def get_ocean_conditions(self, latitude, longitude):
        """Fetch marine conditions (waves, swells) from Open-Meteo Marine API."""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "wave_height,wave_direction,wave_period,swell_wave_height,swell_wave_direction,swell_wave_period",
                "timezone": "auto"
            }
            
            response = requests.get(self.marine_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            
            # Structured to match decision_engine.py expectations
            return {
                "current": {
                    "wave_height": current.get("wave_height"),
                    "wave_direction": current.get("wave_direction"),
                    "wave_period": current.get("wave_period"),
                    "swell_wave_height": current.get("swell_wave_height"),
                    "swell_wave_direction": current.get("swell_wave_direction"),
                    "swell_wave_period": current.get("swell_wave_period")
                },
                "source": "Open-Meteo Marine"
            }
        except Exception as error:
            return {"error": str(error), "current": {}, "source": "Open-Meteo Marine"}

    def get_sea_temperature(self, latitude, longitude):
        """Fetch current sea-surface temperature."""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "sea_surface_temperature",
                "timezone": "auto"
            }
            
            response = requests.get(self.marine_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "current": {
                    "sea_surface_temperature": data.get("current", {}).get("sea_surface_temperature")
                },
                "source": "Open-Meteo Marine"
            }
        except Exception as error:
            return {"error": str(error), "current": {}, "source": "Open-Meteo Marine"}

if __name__ == "__main__":
    import json
    agent = OceanAgent()
    print("Testing OceanAgent near Mangalore...")
    ocean_result = agent.get_ocean_conditions(12.9141, 74.8560)
    print(json.dumps(ocean_result, indent=2))