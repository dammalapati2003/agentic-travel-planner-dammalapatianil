import httpx
from typing import Dict, Any, List

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def geocode_city(city: str) -> Dict[str, Any]:
    """
    Geocode a city name using Open-Meteo geocoding.
    Returns: {"name": str, "lat": float, "lon": float, "country": str?}
    """
    r = httpx.get(GEOCODE_URL, params={"name": city, "count": 1}, timeout=15)
    r.raise_for_status()
    d = r.json()
    results = d.get("results", [])
    if not results:
        raise ValueError(f"City not found: {city}")
    top = results[0]
    return {
        "name": top.get("name", city),
        "lat": top["latitude"],
        "lon": top["longitude"],
        "country": top.get("country"),
    }


def daily_summary(city: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Live daily weather summary using Open-Meteo.
    Returns structure expected by weather_agent:
    {
      "city": "<Resolved City>",
      "days": [
        {"date": "YYYY-MM-DD", "tmin_c": float|None, "tmax_c": float|None,
         "precip_mm": float|None, "summary": "<text>"},
         ...
      ]
    }
    Falls back to current weather if daily arrays are unavailable.
    """
    g = geocode_city(city)
    lat, lon = g["lat"], g["lon"]

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weathercode"],
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        r = httpx.get(FORECAST_URL, params=params, timeout=20)
        r.raise_for_status()
        d = r.json()
        daily = d.get("daily", {})
        times: List[str] = daily.get("time", []) or []

        tmin = daily.get("temperature_2m_min", []) or []
        tmax = daily.get("temperature_2m_max", []) or []
        precip = daily.get("precipitation_sum", []) or []
        codes = daily.get("weathercode", []) or []

        if times and (tmin or tmax or precip or codes):
            days = []
            n = len(times)
            for i in range(n):
                days.append(
                    {
                        "date": times[i],
                        "tmin_c": _safe_get(tmin, i),
                        "tmax_c": _safe_get(tmax, i),
                        "precip_mm": _safe_get(precip, i),
                        "summary": _weather_code_to_summary(_safe_get(codes, i)),
                    }
                )
            return {"city": g.get("name", city), "days": days}
    except Exception:
        pass

    # Fallback
    try:
        rc = httpx.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,precipitation",
                "timezone": "auto",
            },
            timeout=15,
        )
        rc.raise_for_status()
        cur = rc.json().get("current", {}) or {}
        temp = cur.get("temperature_2m")
        prec = cur.get("precipitation")
        # Use start date as the row date 
        return {
            "city": g.get("name", city),
            "days": [
                {
                    "date": start_date,
                    "tmin_c": temp,
                    "tmax_c": temp,
                    "precip_mm": prec,
                    "summary": f"{temp}°C" if temp is not None else "",
                }
            ],
        }
    except Exception as e:
        return {"city": g.get("name", city), "error": f"weather fetch failed: {e}", "days": []}


def _safe_get(arr, i):
    try:
        v = arr[i]
        # cast to float
        return float(v) if v is not None else None
    except Exception:
        return None


def _weather_code_to_summary(code: Any) -> str:
    try:
        c = int(code) if code is not None else None
    except Exception:
        c = None
    mapping = {
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
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(c, "")
