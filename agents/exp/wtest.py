import requests


def get_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


# Test the function
result = get_weather(12.9716, 77.5946)

print(result)