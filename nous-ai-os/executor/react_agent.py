"""ReAct (Reasoning + Acting) Autonomous Loop and Tool Registry for NOUS.

Provides a structured Thought -> Action -> Observation -> Reflection loop with a secure,
extensible dynamic tool registry.
"""
import os
import json
import time
from typing import Any, Callable, Dict, List, Optional

from executor.command_tools import run_command


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
                if not os.path.exists(path):
                    return f"[ERROR]: File not found: {path}"
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                return content[:8000] + ("\n...[truncated]" if len(content) > 8000 else "")
            except Exception as e:
                return f"[ERROR]: {str(e)}"

        def write_file_tool(path: str, content: str) -> str:
            try:
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"[SUCCESS]: Wrote {len(content)} characters to {path}"
            except Exception as e:
                return f"[ERROR]: {str(e)}"

        def list_dir_tool(path: str = ".") -> str:
            try:
                entries = os.listdir(path)
                return json.dumps(entries[:100], ensure_ascii=False)
            except Exception as e:
                return f"[ERROR]: {str(e)}"

        def git_status_tool() -> str:
            return _run_approved_command("git status --short")

        self.register("bash", bash_tool, TOOL_DESCRIPTION, {"cmd": "string"})
        self.register("read_file", read_file_tool, "Reads up to 8KB of a file path.", {"path": "string"})
        self.register("write_file", write_file_tool, "Writes text to a specified file path.", {"path": "string", "content": "string"})
        self.register("list_dir", list_dir_tool, "Lists files and folders inside a directory.", {"path": "string"})
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
            except Exception as e:
                observation = f"[ERROR]: Failed executing {action_name}: {str(e)}"

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
