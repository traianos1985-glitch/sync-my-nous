"""GPS Tracker — αποθηκεύει live θέση από browser geolocation και επιστρέφει track."""
import json, time
from pathlib import Path

STATE_FILE = Path("data/gps_state.json")


def _load() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"positions": [], "last_fix": None}


def _save(s: dict):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def update_position(lat: float, lon: float, accuracy: float = None, source: str = "browser") -> dict:
    s = _load()
    fix = {
        "lat": float(lat),
        "lon": float(lon),
        "accuracy": float(accuracy) if accuracy is not None else None,
        "source": source,
        "ts": time.time(),
        "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    s["last_fix"] = fix
    s["positions"] = (s.get("positions", []) + [fix])[-500:]
    _save(s)
    return fix


def get_last_position() -> dict | None:
    return _load().get("last_fix")


def get_track(limit: int = 100) -> list:
    return _load().get("positions", [])[-limit:]


def clear_track() -> dict:
    s = _load()
    count = len(s.get("positions", []))
    s["positions"] = []
    _save(s)
    return {"ok": True, "cleared": count}


def gps_status() -> dict:
    s = _load()
    last = s.get("last_fix")
    age = (time.time() - last["ts"]) if last else None
    return {
        "has_fix":     last is not None,
        "last_fix":    last,
        "age_seconds": round(age, 1) if age is not None else None,
        "live":        age is not None and age < 30,
        "track_points": len(s.get("positions", [])),
    }
