"""ReAct (Reasoning + Acting) Autonomous Loop and Tool Registry for NOUS.
Provides a structured Thought -> Action -> Observation -> Reflection loop with a secure,
extensible dynamic tool registry.
"""
import os
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from executor.command_tools import run_command

WORKSPACE = Path("data/agent_workspace")


def _resolve_workspace_path(raw_path: str, *, create_workspace: bool = False) -> Path:
    """Resolve a relative agent-workspace path and reject traversal and symlink escapes."""
    if not isinstance(raw_path, str) or not raw_path.strip() or len(raw_path) > 1024:
        raise ValueError("invalid_workspace_path")
    candidate_text = raw_path.strip()
    candidate = Path(candidate_text)
    if candidate.is_absolute():
        raise ValueError("path_outside_workspace")
    root = WORKSPACE.resolve()
    if create_workspace:
        root.mkdir(parents=True, exist_ok=True)
        root = WORKSPACE.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("path_outside_workspace") from exc
    return resolved


def _run_approved_command(cmd: str) -> str:
    return json.dumps(run_command(cmd), ensure_ascii=False)


def _approval_pending(observation: str) -> bool:
    try:
        return bool(json.loads(observation).get("approval_required"))
    except (AttributeError, TypeError, ValueError):
        return False


def _command_failed(observation: str) -> bool:
    try:
        result = json.loads(observation)
        return (result.get("ok") is False or "error" in result) and not result.get("approval_required")
    except (AttributeError, TypeError, ValueError):
        return False


PENDING_MESSAGE = "Command execution is pending explicit operator approval."
FAILED_MESSAGE = "The requested command did not complete."
COMPLETED_MESSAGE = "Read-only inspection completed."
TOOL_DESCRIPTION = "Requests explicit operator approval before running an allowlisted command."
GIT_DESCRIPTION = "Requests explicit operator approval before checking git status."


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register(self, name: str, func: Callable, description: str, parameters: Dict[str, str]):
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters,
        }

    def get(self, name: str) -> Optional[Callable]:
        tool = self._tools.get(name)
        return tool["func"] if tool else None

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": k,
                "description": v["description"],
                "parameters": v["parameters"]
            }
            for k, v in self._tools.items()
        ]

    def _register_default_tools(self):
        def bash_tool(cmd: str) -> str:
            return _run_approved_command(cmd)

        def read_file_tool(path: str) -> str:
            try:
                target = _resolve_workspace_path(path, create_workspace=True)
                if not target.is_file():
                    return "[ERROR]: File not found in agent workspace."
                content = target.read_text(encoding="utf-8", errors="replace")
                return content[:8000] + ("\n...[truncated]" if len(content) > 8000 else "")
            except ValueError as exc:
                return f"[ERROR]: {exc}"
            except OSError:
                return "[ERROR]: Unable to read workspace file."

        def write_file_tool(path: str, content: str) -> str:
            try:
                if not isinstance(content, str) or len(content) > 100_000:
                    return "[ERROR]: Invalid or oversized file content."
                target = _resolve_workspace_path(path, create_workspace=True)
                target.parent.mkdir(parents=True, exist_ok=True)
                # Resolve again after creating parents to reject symlinked parent directories.
                target = _resolve_workspace_path(path)
                target.write_text(content, encoding="utf-8")
                return f"[SUCCESS]: Wrote {len(content)} characters to agent workspace file."
            except ValueError as exc:
                return f"[ERROR]: {exc}"
            except OSError:
                return "[ERROR]: Unable to write workspace file."

        def list_dir_tool(path: str = ".") -> str:
            try:
                target = _resolve_workspace_path(path, create_workspace=True)
                if not target.is_dir():
                    return "[ERROR]: Directory not found in agent workspace."
                entries = sorted(entry.name for entry in target.iterdir())[:100]
                return json.dumps(entries, ensure_ascii=False)
            except ValueError as exc:
                return f"[ERROR]: {exc}"
            except OSError:
                return "[ERROR]: Unable to list workspace directory."

        def git_status_tool() -> str:
            return _run_approved_command("git status --short")

        self.register("bash", bash_tool, TOOL_DESCRIPTION, {"cmd": "string"})
        self.register("read_file", read_file_tool, "Reads up to 8KB from the isolated agent workspace.", {"path": "string"})
        self.register("write_file", write_file_tool, "Writes at most 100KB inside the isolated agent workspace.", {"path": "string", "content": "string"})
        self.register("list_dir", list_dir_tool, "Lists entries inside the isolated agent workspace.", {"path": "string"})
        self.register("git_status", git_status_tool, GIT_DESCRIPTION, {})


GLOBAL_TOOL_REGISTRY = ToolRegistry()


class ReActAgent:
    """ReAct Agent execution loop with step logging and reflection."""
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or GLOBAL_TOOL_REGISTRY

    def execute_step(self, thought: str, action_name: str, action_args: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.registry.get(action_name)
        if not tool:
            observation = f"[ERROR]: Tool '{action_name}' is not registered."
        else:
            try:
                observation = str(tool(**action_args))
            except Exception:
                observation = f"[ERROR]: Failed executing {action_name}."
        return {
            "thought": thought,
            "action": action_name,
            "args": action_args,
            "observation": observation,
            "timestamp": time.time()
        }

    def run(self, task: str, max_steps: int = 5) -> Dict[str, Any]:
        """Runs an autonomous task through the ReAct loop."""
        steps = []
        task_lower = task.lower()
        if any(w in task_lower for w in ["status", "git", "branch"]):
            step = self.execute_step("Checking repository state first.", "git_status", {})
            steps.append(step)
        elif any(w in task_lower for w in ["list", "files", "dir"]):
            step = self.execute_step("Listing directory to inspect files.", "list_dir", {"path": "."})
            steps.append(step)
        else:
            step = self.execute_step("Checking current working directory.", "list_dir", {"path": "."})
            steps.append(step)

        observations = [step["observation"] for step in steps]
        if any(_approval_pending(observation) for observation in observations):
            status = "pending_approval"
            reflection = PENDING_MESSAGE
        elif any(_command_failed(observation) for observation in observations):
            status = "failed"
            reflection = FAILED_MESSAGE
        else:
            status = "completed"
            reflection = COMPLETED_MESSAGE
        return {
            "task": task,
            "status": status,
            "steps": steps,
            "reflection": reflection,
            "finished_at": time.time()
        }


DEFAULT_REACT_AGENT = ReActAgent()


def run_react_task(task: str, max_steps: int = 5) -> Dict[str, Any]:
    return DEFAULT_REACT_AGENT.run(task, max_steps=max_steps)
