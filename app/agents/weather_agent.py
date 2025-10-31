from datetime import datetime
from app.tools import weather as weather_tool

TOOLS = {
    "weather.search": lambda args: weather_tool.daily_summary(
        args["city"], args["start_date"], args["end_date"]
    ),
}


def run(query: str, city: str, start_date: str, end_date: str):
    try:
        obs = TOOLS["weather.search"]({"city": city, "start_date": start_date, "end_date": end_date})
    except Exception as e:
        return f" Error: {e}", None

    if not obs or "days" not in obs or not obs["days"]:
        return f" No live data found for {city}.", None

    city_name = obs.get("city", city)
    lines = []
    emoji = {
        "Clear sky": "",
        "Mainly clear": "",
        "Partly cloudy": "",
        "Overcast": "",
        "Fog": "",
        "Slight rain": "",
        "Moderate rain": "",
        "Heavy rain": "",
        "Thunderstorm": "",
    }

    for day in obs["days"]:
        date = day.get("date", "")
        tmin = day.get("tmin_c")
        tmax = day.get("tmax_c")
        summary = day.get("summary", "")
        icon = emoji.get(summary, "")
        if tmin is None or tmax is None:
            line = f"{icon} {date}: {summary}"
        else:
            line = f"{icon} {date}: {summary}, around {round(tmax)}°C max / {round(tmin)}°C min."
        lines.append(line)

    # Short description for multi day trips
    if len(lines) > 2:
        title = f" Weather Forecast for {city_name} ({start_date} → {end_date}):"
    else:
        title = f"Approx Weather in {city_name}:"

    summary_text = "\n".join(lines)
    message = f"{title}\n{summary_text}"

    
    if any("rain" in d.get("summary", "").lower() for d in obs["days"]):
        message += "\n There’s a chance of rain."
    else:
        message += "\n No rain expected today."

    return message, obs
