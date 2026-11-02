import requests

class WeatherAgent:
    """
    Handles all atmospheric data retrieval and synthesis.
    Structures Open-Meteo data specifically for the Saptha Sagara decision engine.
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.headers = {"User-Agent": "ORCA-MarineAI/1.0"}

    def get_weather(self, latitude, longitude):
        """Fetch current weather conditions."""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m",
                "timezone": "auto"
            }
            
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            
            # Structured explicitly to match decision_engine.py expectations
            return {
                "current": {
                    "temperature": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "precipitation": current.get("precipitation"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "wind_direction": current.get("wind_direction_10m"),
                },
                "source": "Open-Meteo"
            }
        except Exception as error:
            return {"error": str(error), "current": {}, "source": "Open-Meteo"}

    def get_forecast(self, latitude, longitude):
        """Fetch 48-hour weather forecast."""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,wind_direction_10m",
                "forecast_days": 2,
                "timezone": "auto"
            }
            
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            hourly = data.get("hourly", {})
            
            return {
                "time": hourly.get("time", [])[:12],
                "temperature": hourly.get("temperature_2m", [])[:12],
                "precipitation_probability": hourly.get("precipitation_probability", [])[:12],
                "wind_speed": hourly.get("wind_speed_10m", [])[:12],
                "wind_direction": hourly.get("wind_direction_10m", [])[:12],
                "source": "Open-Meteo"
            }
        except Exception as error:
            return {"error": str(error), "source": "Open-Meteo"}

if __name__ == "__main__":
    import json
    agent = WeatherAgent()
    print("Testing WeatherAgent near Mangalore...")
    weather_result = agent.get_weather(12.9141, 74.8560)
    print(json.dumps(weather_result, indent=2))