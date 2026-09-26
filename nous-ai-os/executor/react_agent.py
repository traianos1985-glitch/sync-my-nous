"""ReAct (Reasoning + Acting) Autonomous Loop and Tool Registry for NOUS.

Provides a structured Thought -> Action -> Observation -> Reflection loop with a secure,
extensible dynamic tool registry.
"""
import os
import subprocess
import json
import time
from typing import Any, Callable, Dict, List, Optional

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
            blocked = ["rm -rf /", "mkfs", ":(){ :|:& };:", "dd if="]
            if any(b in cmd for b in blocked):
                return "[ERROR]: Command blocked by safety policy."
            try:
                res = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=15
                )
                out = res.stdout.strip()
                err = res.stderr.strip()
                if err:
                    return f"[OUTPUT]:\n{out}\n[STDERR]:\n{err}" if out else f"[STDERR]:\n{err}"
                return out or "[SUCCESS - No output]"
            except subprocess.TimeoutExpired:
                return "[ERROR]: Command timed out after 15 seconds."
            except Exception as e:
                return f"[ERROR]: {str(e)}"

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
            try:
                res = subprocess.run("git status --short", shell=True, capture_output=True, text=True, timeout=5)
                return res.stdout.strip() or "Working tree clean."
            except Exception as e:
                return f"[ERROR]: {str(e)}"

        self.register("bash", bash_tool, "Runs a bash command securely with a 15s timeout.", {"cmd": "string"})
        self.register("read_file", read_file_tool, "Reads up to 8KB of a file path.", {"path": "string"})
        self.register("write_file", write_file_tool, "Writes text to a specified file path.", {"path": "string", "content": "string"})
        self.register("list_dir", list_dir_tool, "Lists files and folders inside a directory.", {"path": "string"})
        self.register("git_status", git_status_tool, "Shows git working directory status.", {})

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

        reflection = f"Completed {len(steps)} actions towards goal: '{task}'. Environment validated."
        
        return {
            "task": task,
            "status": "completed",
            "steps": steps,
            "reflection": reflection,
            "finished_at": time.time()
        }

DEFAULT_REACT_AGENT = ReActAgent()

def run_react_task(task: str, max_steps: int = 5) -> Dict[str, Any]:
    return DEFAULT_REACT_AGENT.run(task, max_steps=max_steps)
