"""Canonical runtime facade for all NOUS agent entrypoints."""
from __future__ import annotations

from typing import Any

from .agent_core import DEFAULT_AGENT
from .memory_store import get_mem, set_mem


def run(goal: str) -> dict[str, Any]:
    """Run the single canonical agent core while preserving the legacy API shape."""
    result = DEFAULT_AGENT.run(goal, context={"history": get_mem("history", [])[-20:]})
    history = get_mem("history", [])
    history.append({"goal": goal, "status": result["status"]})
    set_mem("history", history[-100:])
    return {"plan": {"goal": goal, "steps": ["analyze", "plugins", "review"]}, "result": result}


__all__ = ["run"]
