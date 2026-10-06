from __future__ import annotations

from typing import Any

from executor.chat_brain_v3 import answer_chat


def chatgpt_style_response(
    message: str,
    conversation_id: str | None = None,
    research_mode: str = "auto",
) -> dict[str, Any] | None:
    return answer_chat(message, conversation_id=conversation_id, research_mode=research_mode)
