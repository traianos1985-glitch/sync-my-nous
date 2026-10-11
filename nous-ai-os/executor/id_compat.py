"""Identifier helpers for browser/API round-trips.

JavaScript Number cannot exactly represent integers above 2**53 - 1. Older
runtime records used nanosecond timestamps as numeric IDs, so a browser could
round an ID before posting it back. Exact matches always win; legacy numeric
fallback is accepted only when it identifies one unique record.
"""
from __future__ import annotations


def new_runtime_id(existing=()):
    """Return a JSON/JavaScript-safe integer ID, unique within *existing*."""
    import time

    value = time.time_ns() // 1_000
    used = {str(item) for item in existing}
    while str(value) in used:
        value += 1
    return value


def find_by_id(items, requested, key="id"):
    """Find by exact ID, with a unique-only compatibility path for legacy IDs."""
    exact = [item for item in items if isinstance(item, dict) and str(item.get(key)) == str(requested)]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return None
    try:
        requested_number = float(requested)
        if not requested_number.is_integer():
            return None
    except (TypeError, ValueError, OverflowError):
        return None
    matches = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            stored_number = float(item.get(key))
            if stored_number.is_integer() and stored_number == requested_number:
                matches.append(item)
        except (TypeError, ValueError, OverflowError):
            continue
    return matches[0] if len(matches) == 1 else None
