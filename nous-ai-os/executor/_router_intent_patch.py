"""Applied into router.chat() — prefer try_intent_route before _chat_intent_route.

This module documents the required router change if the large router.py
push is blocked. The live fix also hardens browser_search so the legacy
path no longer throws.
"""

from __future__ import annotations
from typing import Any


def early_unified_intent(message: str) -> dict[str, Any] | None:
    try:
        from executor.intent_chat_integration import try_intent_route

        return try_intent_route(str(message or ""))
    except Exception:
        return None
