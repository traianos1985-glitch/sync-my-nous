from __future__ import annotations

from typing import Any

from executor.chat_brain_v3 import answer_chat


def chatgpt_style_response(message: str) -> dict[str, Any] | None:
    return answer_chat(message)
