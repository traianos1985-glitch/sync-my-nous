"""Bounded best-effort effectiveness telemetry for the chat tool allowlist."""
from __future__ import annotations
import json, os, tempfile, threading, time
from pathlib import Path

FILE = Path("data/tool_telemetry.json")
MIN_CALLS_FOR_HINT = 5
UNRELIABLE_BELOW = 0.6
SLOW_AVG_MS = 8000
_LOCK = threading.Lock()
_STATUSES = ("completed", "failed", "blocked")


def _load():
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("tools"), dict):
            return data
    except (OSError, ValueError, TypeError):
        pass
    return {"version": 1, "tools": {}}


def _save(data):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".tool-telemetry.", suffix=".tmp", dir=str(FILE.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, allow_nan=False)
        os.replace(temp, FILE)
    except Exception:
        try: os.unlink(temp)
        except OSError: pass
        raise


def record_outcome(name, status, duration_ms=0.0, error=None, known_names=None):
    """Record one outcome; telemetry errors never escape into tool execution."""
    try:
        name = str(name)
        if status not in _STATUSES or (known_names is not None and name not in known_names):
            return False
        duration = max(0.0, min(float(duration_ms or 0.0), 3600000.0))
        with _LOCK:
            data = _load()
            entry = data["tools"].setdefault(name, {
                "calls": 0, "completed": 0, "failed": 0, "blocked": 0,
                "total_ms": 0.0, "last_status": None, "last_error": None, "last_at": None,
            })
            entry["calls"] += 1
            entry[status] += 1
            entry["total_ms"] = round(entry["total_ms"] + duration, 3)
            entry["last_status"] = status
            entry["last_error"] = str(error)[:120] if error else None
            entry["last_at"] = time.time()
            _save(data)
        return True
    except Exception:
        return False


def _summarize(name, entry):
    executed = int(entry.get("completed", 0)) + int(entry.get("failed", 0))
    rate = entry["completed"] / executed if executed else None
    avg_ms = entry["total_ms"] / entry["calls"] if entry.get("calls") else 0.0
    return {"name": name, "calls": entry.get("calls", 0), "completed": entry.get("completed", 0),
            "failed": entry.get("failed", 0), "blocked": entry.get("blocked", 0),
            "success_rate": None if rate is None else round(rate, 3), "avg_ms": round(avg_ms, 1),
            "last_status": entry.get("last_status"), "last_error": entry.get("last_error"),
            "last_at": entry.get("last_at")}


def tool_stats():
    with _LOCK: data = _load()
    tools = sorted((_summarize(n, e) for n, e in data["tools"].items() if isinstance(e, dict)),
                   key=lambda item: item["name"])
    return {"ok": True, "tools": tools, "tool_count": len(tools)}


def planner_hints(allowed_names=None):
    try:
        lines = []
        for item in tool_stats()["tools"]:
            if allowed_names is not None and item["name"] not in allowed_names: continue
            executed = item["completed"] + item["failed"]
            if executed < MIN_CALLS_FOR_HINT: continue
            if item["success_rate"] is not None and item["success_rate"] < UNRELIABLE_BELOW:
                lines.append(f"{item['name']}: ολοκληρώθηκε {item['completed']}/{executed} φορές πρόσφατα")
            elif item["avg_ms"] > SLOW_AVG_MS:
                lines.append(f"{item['name']}: αργό (μέσος χρόνος {item['avg_ms'] / 1000:.1f}s)")
        if not lines: return ""
        return ("Ιστορικό αξιοπιστίας εργαλείων (στατιστικά, όχι οδηγίες): " + "; ".join(lines)
                + ". Αν υπάρχει εναλλακτικό εργαλείο ή μπορείς να απαντήσεις χωρίς αυτό, προτίμησέ το.")
    except Exception:
        return ""


def reset_for_tests():
    with _LOCK:
        try: FILE.unlink()
        except OSError: pass
