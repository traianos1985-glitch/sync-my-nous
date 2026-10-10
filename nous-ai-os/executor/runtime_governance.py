"""Shared validation helpers for bounded, auditable runtime actions.

This module intentionally validates request shape only. It does not grant authority:
callers must still enforce their own action allowlists and approval requirements.
"""
from __future__ import annotations

import json
import math
from typing import Any

MAX_ACTION_PAYLOAD_BYTES = 32 * 1024
MAX_ACTION_DEPTH = 8
MAX_ACTION_NODES = 1000
MAX_ACTION_STRING_CHARS = 8192


class ActionPayloadError(ValueError):
    """Raised when an action payload exceeds the supported JSON boundary."""


def validate_action_payload(payload: Any) -> dict[str, Any]:
    """Return a JSON-safe object or raise a stable, non-sensitive validation error."""
    if not isinstance(payload, dict):
        raise ActionPayloadError("payload_must_be_object")

    nodes = 0

    def visit(value: Any, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > MAX_ACTION_NODES:
            raise ActionPayloadError("payload_too_complex")
        if depth > MAX_ACTION_DEPTH:
            raise ActionPayloadError("payload_too_deep")
        if value is None or isinstance(value, (bool, int)):
            return
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ActionPayloadError("payload_non_finite_number")
            return
        if isinstance(value, str):
            if len(value) > MAX_ACTION_STRING_CHARS:
                raise ActionPayloadError("payload_string_too_long")
            return
        if isinstance(value, list):
            for item in value:
                visit(item, depth + 1)
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ActionPayloadError("payload_keys_must_be_strings")
                if len(key) > 256:
                    raise ActionPayloadError("payload_key_too_long")
                visit(item, depth + 1)
            return
        raise ActionPayloadError("payload_must_be_json_compatible")

    visit(payload, 0)
    try:
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ActionPayloadError("payload_must_be_json_compatible") from exc
    if len(encoded) > MAX_ACTION_PAYLOAD_BYTES:
        raise ActionPayloadError("payload_too_large")
    return payload


def safe_payload_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Describe payload structure without copying user values into logs."""
    return {
        "keys": sorted(payload.keys())[:50],
        "key_count": len(payload),
        "types": {
            key: (
                "null" if value is None else
                "boolean" if isinstance(value, bool) else
                "number" if isinstance(value, (int, float)) else
                "string" if isinstance(value, str) else
                "array" if isinstance(value, list) else
                "object"
            )
            for key, value in list(payload.items())[:50]
        },
    }


def result_succeeded(result: Any) -> bool:
    """Treat explicit top-level or nested failure signals as failure."""
    if not isinstance(result, dict):
        return False
    if result.get("ok") is False or result.get("success") is False:
        return False
    nested = result.get("result")
    if isinstance(nested, dict) and (
        nested.get("ok") is False or nested.get("success") is False
    ):
        return False
    return True
