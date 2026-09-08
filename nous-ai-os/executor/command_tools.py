import subprocess

ALLOWED = [
    "pwd",
    "ls",
    "date",
    "whoami"
]

def run_command(cmd):

    parts = cmd.strip().split()

    if not parts:
        return {"error": "empty_command"}

    if parts[0] not in ALLOWED:
        return {
            "error": "command_blocked",
            "allowed": ALLOWED
        }

    try:
        out = subprocess.check_output(
            parts,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10
        )

        return {"output": out}

    except Exception as e:
        return {"error": str(e)}
