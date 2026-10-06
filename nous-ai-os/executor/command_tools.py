import subprocess

from executor.operator_approval import (
    claim_approved_approval,
    finish_approval,
    request_approval,
)

ALLOWED = ["pwd", "ls", "date", "whoami"]
ALLOWED_COMMANDS = {"git status --short"}


def run_command(cmd, approval_id=None):
    parts = cmd.strip().split()
    if not parts:
        return {"error": "empty_command"}

    if parts[0] not in ALLOWED and cmd.strip() not in ALLOWED_COMMANDS:
        return {"error": "command_blocked", "allowed": [*ALLOWED, *sorted(ALLOWED_COMMANDS)]}

    payload = {"command": cmd}
    if not approval_id:
        approval = request_approval(
            "command_execution",
            payload,
            "Shell command requires explicit approval",
        )
        return {
            "ok": False,
            "approval_required": True,
            "approval_id": str(approval["id"]),
            "command": cmd,
        }

    approval = claim_approved_approval(approval_id, "command_execution", payload)
    if not approval:
        return {"ok": False, "error": "valid_approval_required"}

    try:
        output = subprocess.check_output(
            parts,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
        result = {"ok": True, "output": output}
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}

    finish_approval(
        approval_id,
        "completed" if result["ok"] else "failed",
        result,
    )
    return result
