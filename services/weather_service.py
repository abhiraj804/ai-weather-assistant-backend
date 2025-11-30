import httpx

async def get_current_weather(lat: float, lon: float):
    """Fetches current weather and tomorrow's forecast from Open-Meteo"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,is_day,precipitation,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max",
        "forecast_days": 2  # Today and tomorrow
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        
    return {
        "current": data.get("current", {}),
        "daily": data.get("daily", {})
    }