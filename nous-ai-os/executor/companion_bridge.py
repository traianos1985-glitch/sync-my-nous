import time
from executor.code_assistant import run_cmd

PKG = "com.nous.companion"
RECEIVER = "com.nous.companion/.CommandReceiver"
ACTION = "com.nous.companion.COMMAND"


def _broadcast(command, extras=""):
    cmd = f'am broadcast -a {ACTION} -n {RECEIVER} --es command {command} {extras}'
    result = run_cmd(cmd)
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
        "available": True,
        "commands": ["home", "back", "ui_tree", "tap"],
        "time": time.time(),
    }


def companion_home():
    return _broadcast("home")


def companion_back():
    return _broadcast("back")


def companion_ui_tree():
    return _broadcast("ui_tree")


def companion_tap(x, y):
    return _broadcast("tap", f"--ef x {float(x)} --ef y {float(y)}")


def companion_logs(lines=80):
    result = run_cmd(f'logcat -d | grep -i "NOUS_COMPANION" | tail -{int(lines)}')
    return {
        "ok": bool(result.get("ok")),
        "lines": lines,
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
