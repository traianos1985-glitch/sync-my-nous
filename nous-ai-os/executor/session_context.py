"""Lightweight per-process session context for multi-turn clarifications."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_PATH = Path("data/chat_session_context.json")
_MAX_AGE_SEC = 30 * 60


def _load() -> dict[str, Any]:
    try:
        if _PATH.exists():
            data = json.loads(_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _save(data: dict[str, Any]) -> None:
    try:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        _PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def remember_classification(classification: dict[str, Any], message: str = "") -> None:
    data = _load()
    data["last"] = {
        "ts": time.time(),
        "message": (message or "")[:500],
        "intent": classification.get("intent"),
        "confidence": classification.get("confidence"),
        "slots": classification.get("slots") or {},
        "needs_clarification": bool(classification.get("needs_clarification")),
        "clarification_question": classification.get("clarification_question"),
    }
    _save(data)


def get_last() -> dict[str, Any] | None:
    data = _load()
    last = data.get("last")
    if not isinstance(last, dict):
        return None
    ts = float(last.get("ts") or 0)
    if time.time() - ts > _MAX_AGE_SEC:
        return None
    return last


def clear() -> None:
    _save({})
