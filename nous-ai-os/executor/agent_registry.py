"""Single source of truth for the NOUS agent surface."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from .agent_core import DEFAULT_AGENT, AgentCore


@dataclass(frozen=True, slots=True)
class AgentPluginSpec:
    name: str
    module: str
    status: str = "legacy-adapter"


LEGACY_MODULES = (
    AgentPluginSpec("autonomous", "autonomous_agent"),
    AgentPluginSpec("research", "research_agent"),
    AgentPluginSpec("scheduler", "scheduler_agent"),
    AgentPluginSpec("browser", "research_browser_agent"),
    AgentPluginSpec("repair", "repair_agent"),
)


def get_core() -> AgentCore:
    return DEFAULT_AGENT


def load_legacy(name: str) -> Any:
    """Load a legacy adapter only at an explicit compatibility boundary."""
    spec = next((item for item in LEGACY_MODULES if item.name == name), None)
    if spec is None:
        raise KeyError(f"Unknown legacy agent: {name}")
    return import_module(f"{__package__}.{spec.module}")


__all__ = ["AgentPluginSpec", "LEGACY_MODULES", "get_core", "load_legacy"]
