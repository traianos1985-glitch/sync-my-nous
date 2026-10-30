"""Shared policy for detecting agent goals that invoke Code Forge.

Keep the approval gate and the executor's dispatch decision on the same
classifier so a goal cannot be approved under one rule and executed under
another.
"""
from __future__ import annotations

import re
import unicodedata


_CODEGEN_TERMS = {"plugin", "plugins", "calculator", "code"}
_GREEK_CODE_STEMS = ("κωδικ",)


def _tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return set(re.findall(r"[^\\W_]+", normalized, flags=re.UNICODE))


def requires_code_generation(goal: str) -> bool:
    """Return whether solve_goal's Code Forge branch will be invoked."""
    tokens = _tokens(goal)
    return bool(tokens & _CODEGEN_TERMS) or any(
        token.startswith(stem)
        for token in tokens
        for stem in _GREEK_CODE_STEMS
    )
