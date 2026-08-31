import httpx

# WMO Weather interpretation codes (WW)
# https://open-meteo.com/en/docs
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _get_description(code: int) -> str:
    return WMO_CODES.get(code, "Unknown weather")


def _geocode(location: str) -> tuple[float, float, str]:
    """Returns (latitude, longitude, resolved_name)."""
    resp = httpx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Location not found: {location}")

    first = results[0]
    return first.get("latitude"), first.get("longitude"), first.get("name")


def get_current_weather(location: str) -> dict:
    lat, lon, resolved_name = _geocode(location)

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "weather_code",
        ],
    }

    resp = httpx.get(
        "https://api.open-meteo.com/v1/forecast", params=params, timeout=15.0
    )
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current", {})
    return {
        "location_name": resolved_name,
        "temperature": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_description": _get_description(current.get("weather_code", -1)),
    }


def get_forecast(location: str, days: int = 3) -> list[dict]:
    lat, lon, resolved_name = _geocode(location)

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ],
        "forecast_days": days,
    }

    resp = httpx.get(
        "https://api.open-meteo.com/v1/forecast", params=params, timeout=15.0
    )
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily", {})
    times = daily.get("time", [])

    results = []
    for i in range(len(times)):
        results.append(
            {
                "date": times[i],
                "high": daily.get("temperature_2m_max", [])[i],
                "low": daily.get("temperature_2m_min", [])[i],
                "description": _get_description(daily.get("weather_code", [])[i]),
                "precipitation_chance": daily.get("precipitation_probability_max", [])[
                    i
                ],
            }
        )

    return results
