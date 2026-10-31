import os
import time
from executor.code_assistant import run_cmd

PKG = "com.nous.companion"
PAIRING_TOKEN_ENV = "NOUS_COMPANION_PAIRING_TOKEN"
RECEIVER = "com.nous.companion/.CommandReceiver"
ACTION = "com.nous.companion.COMMAND"


def _broadcast(command, extras=None):
    token = os.environ.get(PAIRING_TOKEN_ENV, "").strip()
    if not token:
        return {
            "ok": False,
            "command": command,
            "error": "companion_pairing_token_not_configured",
            "time": time.time(),
        }
    argv = ["am", "broadcast", "-a", ACTION, "-n", RECEIVER, "--es", "command", command,
            "--es", "pairing_token", token]
    if extras:
        argv.extend(extras)
    result = run_cmd(argv)
    return {
        "ok": bool(result.get("ok")),
        "command": command,
        "result": result,
        "time": time.time(),
    }


def companion_status():
    return {
        "package": PKG,
        "receiver": RECEIVER,
        "available": bool(os.environ.get(PAIRING_TOKEN_ENV, "").strip()),
        "pairing_configured": bool(os.environ.get(PAIRING_TOKEN_ENV, "").strip()),
        "commands": ["home", "back", "ui_tree", "tap", "state"],
        "time": time.time(),
    }


def companion_home():
    return _broadcast("home")


def companion_back():
    return _broadcast("back")


def companion_ui_tree():
    return _broadcast("ui_tree")


def companion_tap(x, y):
    return _broadcast("tap", ["--ef", "x", str(float(x)), "--ef", "y", str(float(y))])


def companion_logs(lines=80):
    safe_lines = max(1, min(int(lines), 500))
    result = run_cmd(["logcat", "-d"])
    if result.get("ok"):
        filtered = [line for line in result.get("stdout", "").splitlines() if "nous_companion" in line.lower()]
        result["stdout"] = "\n".join(filtered[-safe_lines:])
    return {
        "ok": bool(result.get("ok")),
        "lines": safe_lines,
        "result": result,
        "time": time.time(),
    }


def companion_ui_tree_with_logs():
    sent = companion_ui_tree()
    logs = companion_logs(120)
    return {
        "sent": sent,
        "logs": logs,
        "time": time.time(),
    }
