"""
Field Diary Engine — καταχωρήσεις πεδίου χρυσοθηρίας.
Αποθηκεύει ευρήματα, GPS, φωτογραφίες και AI αναλύσεις.
"""
import json
import os
import uuid
import base64
from datetime import datetime, timezone
from pathlib import Path

FIELD_DIR = Path("data/field_diary")
ENTRIES_FILE = FIELD_DIR / "entries.json"
IMAGES_DIR = FIELD_DIR / "images"

ENTRY_TYPES = {
    "sign":     "🔣 Σημάδι/Σύμβολο",
    "cache":    "📦 Cache/Ταφή",
    "terrain":  "🏔️ Τοπογραφία",
    "frp":      "📍 Σημείο Αναφοράς (FRP)",
    "irp":      "🗺️ Γενική Αναφορά (IRP)",
    "anomaly":  "⚡ Ανωμαλία Εδάφους",
    "find":     "✨ Εύρημα",
    "note":     "📝 Σημείωση",
}


def _load() -> list:
    if not ENTRIES_FILE.exists():
        return []
    try:
        return json.loads(ENTRIES_FILE.read_text("utf-8"))
    except Exception:
        return []


def _save(entries: list) -> None:
    FIELD_DIR.mkdir(parents=True, exist_ok=True)
    ENTRIES_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), "utf-8")


def add_entry(title: str, note: str = "", lat: float | None = None,
              lon: float | None = None, entry_type: str = "note",
              tags: list | None = None, image_path: str = "",
              analysis: str = "") -> dict:
    entries = _load()
    entry = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "title": title.strip(),
        "note": note.strip(),
        "lat": lat,
        "lon": lon,
        "type": entry_type if entry_type in ENTRY_TYPES else "note",
        "tags": tags or [],
        "image_path": image_path,
        "analysis": analysis,
    }
    entries.insert(0, entry)
    _save(entries)
    return {"ok": True, "entry": entry}


def list_entries(limit: int = 50, entry_type: str | None = None) -> list:
    entries = _load()
    if entry_type:
        entries = [e for e in entries if e.get("type") == entry_type]
    return entries[:limit]


def get_entry(entry_id: str) -> dict | None:
    for e in _load():
        if e.get("id") == entry_id:
            return e
    return None


def update_entry(entry_id: str, **kwargs) -> dict:
    entries = _load()
    for e in entries:
        if e.get("id") == entry_id:
            for k, v in kwargs.items():
                if k not in ("id", "timestamp"):
                    e[k] = v
            _save(entries)
            return {"ok": True, "entry": e}
    return {"ok": False, "error": "not_found"}


def delete_entry(entry_id: str) -> dict:
    entries = _load()
    before = len(entries)
    entries = [e for e in entries if e.get("id") != entry_id]
    _save(entries)
    return {"ok": len(entries) < before}


def save_field_image(file_data: bytes, filename: str) -> str:
    """Save uploaded image, return relative path."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_")
    path = IMAGES_DIR / (ts + safe)
    path.write_bytes(file_data)
    return str(path)


def get_map_markers() -> list:
    """Return all entries that have GPS coords, formatted for Leaflet."""
    markers = []
    for e in _load():
        if e.get("lat") is not None and e.get("lon") is not None:
            markers.append({
                "id":    e["id"],
                "lat":   e["lat"],
                "lon":   e["lon"],
                "title": e["title"],
                "type":  e["type"],
                "icon":  ENTRY_TYPES.get(e["type"], "📝"),
                "note":  e["note"][:120] if e.get("note") else "",
                "ts":    e["timestamp"][:10],
            })
    return markers
