"""Weather engine — καιρός Μεσσηνίας via open-meteo.com (free, no API key)."""
import json, time, requests
from pathlib import Path

MESSINIA_LAT = 37.07
MESSINIA_LON = 22.10
CACHE_FILE   = Path("data/weather_cache.json")
CACHE_TTL    = 1800  # 30 minutes

WMO_CODES = {
    0: "☀️ Αίθριος", 1: "🌤️ Κυρίως αίθριος", 2: "⛅ Μερικώς συννεφιά",
    3: "☁️ Συννεφιά", 45: "🌫️ Ομίχλη", 48: "🌫️ Πάγος",
    51: "🌦️ Ψιλόβροχο", 53: "🌦️ Βροχή", 55: "🌧️ Βαριά βροχή",
    61: "🌧️ Ελαφρά βροχή", 63: "🌧️ Βροχή", 65: "🌧️ Έντονη βροχή",
    71: "🌨️ Χιόνι", 80: "🌦️ Ραγδαία βροχή", 81: "🌧️ Ισχυρή βροχή",
    95: "⛈️ Καταιγίδα", 99: "⛈️ Ισχυρή καταιγίδα",
}

def get_weather(force_refresh: bool = False) -> dict:
    if not force_refresh and CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if time.time() - cached.get("fetched_at", 0) < CACHE_TTL:
                return cached
        except Exception:
            pass

    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": MESSINIA_LAT,
                "longitude": MESSINIA_LON,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
                "timezone": "Europe/Athens",
                "forecast_days": 3,
            },
            timeout=10,
        )
        data = r.json()
        current = data.get("current", {})
        daily   = data.get("daily", {})
        wcode   = current.get("weather_code", 0)

        result = {
            "ok": True,
            "fetched_at": time.time(),
            "location": "Μεσσηνία, Ελλάδα",
            "current": {
                "temp":        current.get("temperature_2m"),
                "humidity":    current.get("relative_humidity_2m"),
                "wind_kmh":    current.get("wind_speed_10m"),
                "rain_mm":     current.get("precipitation"),
                "code":        wcode,
                "description": WMO_CODES.get(wcode, "Άγνωστος"),
            },
            "forecast": [],
            "field_recommendation": _field_recommendation(current),
        }

        for i in range(min(3, len(daily.get("time", [])))):
            dcode = (daily.get("weather_code") or [0])[i]
            result["forecast"].append({
                "date":        (daily.get("time") or [""])[i],
                "max":         (daily.get("temperature_2m_max") or [None])[i],
                "min":         (daily.get("temperature_2m_min") or [None])[i],
                "rain":        (daily.get("precipitation_sum") or [0])[i],
                "description": WMO_CODES.get(dcode, "—"),
            })

        CACHE_FILE.parent.mkdir(exist_ok=True)
        CACHE_FILE.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


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
