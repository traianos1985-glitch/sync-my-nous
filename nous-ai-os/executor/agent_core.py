"""Canonical NOUS agent runtime with plugin hooks.

Legacy agent modules should depend on this core rather than implement their own
planning/execution loops. Plugins are intentionally small and composable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class AgentPlugin(Protocol):
    name: str

    def before_run(self, context: dict[str, Any]) -> dict[str, Any]: ...

    def after_run(self, context: dict[str, Any], result: Any) -> Any: ...


@dataclass(slots=True)
class AgentCore:
    plugins: list[AgentPlugin] = field(default_factory=list)

    def run(self, task: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        state = {"task": task, **(context or {})}
        for plugin in self.plugins:
            state = plugin.before_run(state)
        result: dict[str, Any] = {
            "ok": True,
            "task": task,
            "status": "planned",
            "context": state,
            "approval_required": True,
        }
        for plugin in reversed(self.plugins):
            result = plugin.after_run(state, result)
        return result


class AuditPlugin:
    name = "audit"

    def before_run(self, context: dict[str, Any]) -> dict[str, Any]:
        return {**context, "audit": {"phase": "before_run"}}

    def after_run(self, context: dict[str, Any], result: Any) -> Any:
        return {**result, "audit": {"phase": "after_run", "task": context["task"]}}


DEFAULT_AGENT = AgentCore(plugins=[AuditPlugin()])

def act(task: str, context: dict[str, Any] | None = None) -> Any:
    return DEFAULT_AGENT.run(task, context=context)


__all__ = ["AgentCore", "AgentPlugin", "AuditPlugin", "DEFAULT_AGENT", "act"]
