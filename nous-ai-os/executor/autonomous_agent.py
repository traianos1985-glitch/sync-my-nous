"""Safe, inspectable autonomy layer for NOUS.

The agent can plan, inspect the workspace, propose code changes, and run read-only
verification. Mutating actions are represented as approval requests; nothing is
silently applied to the host or pushed to GitHub.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from executor.agent_journal import verify_journal, write_journal

ROOT = Path(os.getenv("NOUS_WORKSPACE", ".")).resolve()
STATE = ROOT / "data" / "autonomous_agent_state.json"
MAX_READ = 20_000
ALLOWED_CHECKS = {"python_compile", "git_diff_check", "journal_integrity"}
MAX_CHECK_ATTEMPTS = 2


def _state() -> dict[str, Any]:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"proposals": [], "runs": []}


def _save(state: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_path(relative: str) -> Path:
    candidate = (ROOT / relative).resolve()
    if candidate != ROOT and ROOT not in candidate.parents:
        raise ValueError("Η διαδρομή είναι εκτός workspace.")
    return candidate


def capabilities() -> dict[str, Any]:
    return {
        "ok": True,
        "mode": "proposal_first",
        "capabilities": ["plan", "inspect_files", "propose_code", "verify_python", "remember_state"],
        "requires_approval": ["write_files", "run_commands", "browser_actions", "deploy", "git_push"],
        "self_awareness": {
            "meaning": "Ο ΝΟΥΣ αναφέρει μόνο επιβεβαιωμένες ενέργειες και διαχωρίζει προτάσεις από εκτελέσεις.",
            "workspace": str(ROOT),
        },
    }


def inspect_file(path: str) -> dict[str, Any]:
    target = _safe_path(path)
    if not target.is_file():
        return {"ok": False, "error": "file_not_found"}
    content = target.read_text(encoding="utf-8", errors="replace")[:MAX_READ]
    return {"ok": True, "path": path, "content": content, "truncated": target.stat().st_size > MAX_READ}


def propose_code(goal: str, path: str, content: str) -> dict[str, Any]:
    if not goal.strip() or not path.strip() or not content.strip():
        return {"ok": False, "error": "goal_path_content_required"}
    target = _safe_path(path)
    if target.suffix == ".py":
        try:
            ast.parse(content)
        except SyntaxError as exc:
            return {"ok": False, "error": f"invalid_python: {exc}"}
    proposal = {
        "id": uuid.uuid4().hex,
        "created_at": time.time(),
        "goal": goal.strip(),
        "path": path,
        "content": content,
        "status": "pending_approval",
    }
    state = _state()
    state["proposals"].append(proposal)
    _save(state)
    write_journal("agent_code_proposal_created", {"id": proposal["id"], "path": path, "goal": goal})
    return {"ok": True, "proposal": {k: v for k, v in proposal.items() if k != "content"}, "requires_approval": True}


def run_check(check: str, path: str | None = None) -> dict[str, Any]:
    if check not in ALLOWED_CHECKS:
        return {"ok": False, "error": "check_not_allowed", "allowed": sorted(ALLOWED_CHECKS)}
    if check == "journal_integrity":
        return {"check": check, **verify_journal()}
    if check == "python_compile":
        target = _safe_path(path or "")
        if target.suffix != ".py":
            return {"ok": False, "error": "python_file_required"}
        command = ["python", "-m", "py_compile", str(target)]
    else:
        command = ["git", "diff", "--check"]
    last_output = ""
    for attempt in range(MAX_CHECK_ATTEMPTS):
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=15)
            last_output = (result.stdout + result.stderr)[-4000:]
            if result.returncode == 0:
                return {"ok": True, "check": check, "attempts": attempt + 1, "output": last_output}
        except (OSError, subprocess.TimeoutExpired) as exc:
            last_output = str(exc)
    return {"ok": False, "check": check, "attempts": MAX_CHECK_ATTEMPTS, "output": last_output}


def run_agent(goal: str, path: str | None = None, content: str | None = None) -> dict[str, Any]:
    """Create an auditable plan; never mutates files without explicit approval."""
    if not goal.strip():
        return {"ok": False, "error": "goal_required"}
    result: dict[str, Any] = {"ok": True, "goal": goal.strip(), "steps": ["inspect", "plan", "verify", "request approval for changes"]}
    if path:
        result["inspection"] = inspect_file(path)
    if path and content:
        result["proposal"] = propose_code(goal, path, content)
    state = _state()
    state["runs"].append({"id": uuid.uuid4().hex, "at": time.time(), "goal": goal.strip(), "result": result})
    state["runs"] = state["runs"][-100:]
    _save(state)
    write_journal("agent_run_planned", {"goal": goal, "path": path})
    return result


def pending_proposals() -> dict[str, Any]:
    return {"ok": True, "proposals": [p for p in _state().get("proposals", []) if p.get("status") == "pending_approval"]}


def approve_proposal(proposal_id: str) -> dict[str, Any]:
    state = _state()
    for proposal in state.get("proposals", []):
        if proposal.get("id") == proposal_id:
            proposal["status"] = "approved_not_applied"
            _save(state)
            write_journal("agent_code_proposal_approved", {"id": proposal_id})
            return {"ok": True, "status": proposal["status"], "note": "Έγκριση καταγράφηκε. Η εφαρμογή κώδικα παραμένει ξεχωριστό, ελεγχόμενο βήμα."}
    return {"ok": False, "error": "proposal_not_found"}
