from __future__ import annotations

from typing import Any

from executor.chat_brain_v3 import answer_chat
from executor.intent_chat_integration import try_intent_route


def chatgpt_style_response(
    message: str,
    conversation_id: str | None = None,
    research_mode: str = "auto",
) -> dict[str, Any] | None:
    # Natural-language intent understanding first (status, health, missions, …).
    # Asks clarification when unsure instead of failing or guessing.
    routed = try_intent_route(message)
    if routed is not None:
        return routed
    return answer_chat(message, conversation_id=conversation_id, research_mode=research_mode)
