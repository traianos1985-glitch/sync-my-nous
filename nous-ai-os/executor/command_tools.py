import subprocess

from executor.operator_approval import (
    claim_approved_approval,
    finish_approval,
    request_approval,
)

ALLOWED = ["pwd", "ls", "date", "whoami"]
ALLOWED_COMMANDS = {"git status --short"}
_ALLOWED_ARGUMENTS = {
    "pwd": {()},
    "whoami": {()},
    "date": {()},
    "ls": {
        (), ("-a",), ("-l",), ("-la",), ("-al",), ("-1",), ("-lh",), (".",),
        ("-a", "."), ("-l", "."), ("-la", "."), ("-al", "."), ("-1", "."), ("-lh", "."),
    },
}


def run_command(cmd, approval_id=None):
    if not isinstance(cmd, str) or not cmd.strip():
        return {"error": "empty_command"}
    if len(cmd) > 512 or any(ord(char) < 32 and char != "\\t" for char in cmd):
        return {"error": "invalid_command"}
    normalized = cmd.strip()
    parts = normalized.split()
    if not parts:
        return {"error": "empty_command"}

    if normalized in ALLOWED_COMMANDS:
        pass
    elif parts[0] not in ALLOWED:
        return {"error": "command_blocked", "allowed": [*ALLOWED, *sorted(ALLOWED_COMMANDS)]}
    elif tuple(parts[1:]) not in _ALLOWED_ARGUMENTS.get(parts[0], set()):
        return {
            "error": "command_arguments_blocked",
            "command": parts[0],
            "allowed_arguments": [list(args) for args in sorted(_ALLOWED_ARGUMENTS.get(parts[0], set()))],
        }

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
