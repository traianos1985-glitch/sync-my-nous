"""Weather engine — καιρός Μεσσηνίας via open-meteo.com (free, no API key)."""
import json, time, requests
from pathlib import Path

DEFAULT_LOCATION = "Μεσσηνία"
DEFAULT_LAT = 37.07
DEFAULT_LON = 22.10
CACHE_FILE = Path("data/weather_cache.json")
CACHE_TTL = 1800

WMO_CODES = {
    0: "☀️ Αίθριος", 1: "🌤️ Κυρίως αίθριος", 2: "⛅ Μερικώς συννεφιά",
    3: "☁️ Συννεφιά", 45: "🌫️ Ομίχλη", 48: "🌫️ Πάγος",
    51: "🌦️ Ψιλόβροχο", 53: "🌦️ Βροχή", 55: "🌧️ Βαριά βροχή",
    61: "🌧️ Ελαφρά βροχή", 63: "🌧️ Βροχή", 65: "🌧️ Έντονη βροχή",
    71: "🌨️ Χιόνι", 80: "🌦️ Ραγδαία βροχή", 81: "🌧️ Ισχυρή βροχή",
    95: "⛈️ Καταιγίδα", 99: "⛈️ Ισχυρή καταιγίδα",
}

def _load_cache() -> dict:
    try:
        cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if isinstance(cached.get("locations"), dict):
            return cached
        if cached.get("ok"):
            return {"locations": {DEFAULT_LOCATION.casefold(): cached}}
    except (OSError, ValueError, AttributeError):
        pass
    return {"locations": {}}


def _resolve_location(location: str) -> dict | None:
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1, "language": "el", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return None
    place = results[0]
    labels = [place.get("name"), place.get("admin1"), place.get("country")]
    display = ", ".join(dict.fromkeys(label for label in labels if label))
    return {"latitude": place["latitude"], "longitude": place["longitude"], "display": display}


def get_weather(force_refresh: bool = False, location: str | None = None) -> dict:
    requested_location = (location or DEFAULT_LOCATION).strip()
    cache_key = requested_location.casefold()
    cache = _load_cache()
    cached = cache["locations"].get(cache_key)
    if not force_refresh and cached and time.time() - cached.get("fetched_at", 0) < CACHE_TTL:
        return cached

    try:
        if location:
            place = _resolve_location(requested_location)
            if not place:
                return {"ok": False, "error": "location_not_found"}
            latitude, longitude, display_location = place["latitude"], place["longitude"], place["display"]
        else:
            latitude, longitude, display_location = DEFAULT_LAT, DEFAULT_LON, "Μεσσηνία, Ελλάδα"

        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        daily = data.get("daily", {})
        wcode = current.get("weather_code", 0)

        result = {
            "ok": True,
            "fetched_at": time.time(),
            "location": display_location,
            "current": {
                "temp": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_kmh": current.get("wind_speed_10m"),
                "rain_mm": current.get("precipitation"),
                "code": wcode,
                "description": WMO_CODES.get(wcode, "Άγνωστος"),
            },
            "forecast": [],
            "field_recommendation": _field_recommendation(current),
        }

        for i in range(min(3, len(daily.get("time", [])))):
            dcode = (daily.get("weather_code") or [0])[i]
            result["forecast"].append({
                "date": (daily.get("time") or [""])[i],
                "max": (daily.get("temperature_2m_max") or [None])[i],
                "min": (daily.get("temperature_2m_min") or [None])[i],
                "rain": (daily.get("precipitation_sum") or [0])[i],
                "description": WMO_CODES.get(dcode, "—"),
            })

        cache["locations"][cache_key] = result
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        return result
    except Exception:
        return {"ok": False, "error": "weather_unavailable"}


def _field_recommendation(current: dict) -> str:
    temp = current.get("temperature_2m", 20) or 20
    rain = current.get("precipitation", 0) or 0
    wind = current.get("wind_speed_10m", 0) or 0
    if rain > 2:
        return "❌ Ακατάλληλο για πεδίο — βροχή"
    if wind > 40:
        return "⚠️ Δύσκολο — ισχυρός άνεμος"
    if temp > 38:
        return "⚠️ Πολύ ζέστη — πρωινές ώρες μόνο"
    if temp < 5:
        return "🧥 Κρύο — χρειάζεται ζεστό ντύσιμο"
    if rain == 0 and 15 <= temp <= 32:
        return "✅ Άριστες συνθήκες για πεδίο!"
    return "✅ Καλές συνθήκες για πεδίο"


def weather_status() -> dict:
    w = get_weather()
    if not w.get("ok"):
        return {"available": False, "error": w.get("error")}
    c = w["current"]
    return {
        "available": True,
        "summary": f"{c['description']} {c['temp']}°C, άνεμος {c['wind_kmh']} km/h",
        "recommendation": w["field_recommendation"],
        "forecast_days": len(w.get("forecast", [])),
    }
