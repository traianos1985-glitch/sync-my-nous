"""Small, bounded summaries for audit logs.

Audit trails should explain what happened without duplicating arbitrary payloads or
subsystem output that may contain credentials, prompts, personal data, or URLs.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SENSITIVE_KEY_PARTS = (
    "token", "secret", "password", "api_key", "apikey", "authorization",
    "cookie", "credential", "private_key", "access_key", "refresh_key",
)


def payload_fingerprint(value: Any) -> str:
    """Return a stable digest for binding an approval to the exact action intent."""
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_summary(value: Any, *, max_keys: int = 40) -> dict[str, Any]:
    """Summarize nested output without storing arbitrary values."""
    if not isinstance(value, dict):
        return {"type": type(value).__name__}
    keys = sorted(str(key) for key in value.keys())
    safe_types = {}
    for key, item in list(value.items())[:max_keys]:
        key_text = str(key)
        safe_types[key_text[:120]] = (
            "redacted" if any(part in key_text.lower() for part in SENSITIVE_KEY_PARTS)
            else "null" if item is None
            else "boolean" if isinstance(item, bool)
            else "number" if isinstance(item, (int, float))
            else "string" if isinstance(item, str)
            else "array" if isinstance(item, list)
            else "object" if isinstance(item, dict)
            else type(item).__name__
        )
    summary: dict[str, Any] = {
        "type": "object",
        "key_count": len(keys),
        "keys": keys[:max_keys],
        "value_types": safe_types,
    }
    for key in ("ok", "success", "status", "action", "error", "code"):
        item = value.get(key)
        if isinstance(item, (bool, int, float)) or (
            key in {"status", "action", "error", "code"} and isinstance(item, str)
        ):
            summary[key] = item if not isinstance(item, str) else item[:120]
    if len(keys) > max_keys:
        summary["keys_truncated"] = True
    return summary
