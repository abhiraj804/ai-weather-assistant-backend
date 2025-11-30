import httpx
import geocoder

# Location Coordinates (Fallback)
FALLBACK_LAT = 12.9165
FALLBACK_LON = 79.1325
FALLBACK_CITY = "Vellore"

async def get_location_name(lat: float, lon: float):
    """Reverse geocoding to get City Name using Geocoder (Arcgis)"""
    try:
        g = geocoder.arcgis([lat, lon], method='reverse')
        if g and g.address:
            # Prefer city, then town, then village, then locality
            city = g.city or g.town or g.village
            if city:
                return city
            # Parse address: prefer city-level (second part) over locality (first part)
            parts = [p.strip() for p in g.address.split(',') if p.strip() and p.strip().lower() != 'locating']
            for part in parts[1:]:  # Skip first (locality), check others
                if part and len(part) > 3 and not part.isdigit():
                    return part
            # Fallback to first part if no better
            for part in parts:
                if part and len(part) > 3 and not part.isdigit():
                    return part
    except Exception as e:
        print(f"Geocoding Error: {e}")
    return "Unknown Location"

def resolve_coordinates(lat, lon, client_ip):
    """
    1. Prefer GPS (lat/lon provided)
    2. Fallback to IP Geolocation
    3. Fallback to Vellore (Dev mode)
    """
    if lat is not None and lon is not None:
        return lat, lon

    # Try IP-based
    try:
        if client_ip and client_ip != "127.0.0.1":
            g = geocoder.ip(client_ip)
            if g.latlng:
                return g.latlng[0], g.latlng[1]
    except Exception:
        pass
    
    # Final Fallback
    print("Using Fallback: Vellore")
    return FALLBACK_LAT, FALLBACK_LON


async def get_coordinates_from_city(city_name: str):
    """Converts 'Tokyo' -> (35.6, 139.6) using Geocoder"""
    try:
        g = geocoder.arcgis(city_name)
        if g and g.latlng:
            lat, lon = g.latlng
            # Use the city name or first part of address
            name = city_name  # Or g.city if available, but arcgis may not have
            return lat, lon, name
    except Exception as e:
        print(f"Geocoding Error: {e}")
    return None, None, None