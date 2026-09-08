import subprocess
import time
from executor.android_control import android_status, android_notify, android_open_url
from executor.guardian_policy import check_action
from executor.agent_journal import write_journal

ALLOWED_PACKAGES = {
    "settings": "com.android.settings",
}

def _cmd(command):
    try:
        p = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=15)
        return {"ok": p.returncode == 0, "code": p.returncode, "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def android_actions_status():
    return {
        "mode": "safe_allowlist",
        "allowed": ["status", "notify", "open_url", "open_settings"],
        "blocked": ["tap", "send_sms", "send_email", "delete", "install", "payments"],
        "allowed_packages": ALLOWED_PACKAGES,
        "time": time.time(),
    }

def open_allowed_app(name):
    name = str(name).strip().lower()
    if name not in ALLOWED_PACKAGES:
        return {"ok": False, "error": "app_not_allowed", "allowed": list(ALLOWED_PACKAGES.keys())}

    policy = check_action("android_open_url")
    if not policy.get("allowed"):
        return {"ok": False, "policy": policy}

    pkg = ALLOWED_PACKAGES[name]
    result = _cmd(f"monkey -p {pkg} 1")
    write_journal("android_open_allowed_app", {"name": name, "package": pkg, "result": result})
    return result

def run_android_action(action, payload=None):
    payload = payload or {}
    action = str(action)

    if action == "status":
        return android_status()
    if action == "notify":
        return android_notify(payload.get("title", "ΝΟΥΣ AI"), payload.get("message", "Ο ΝΟΥΣ είναι ενεργός"))
    if action == "open_url":
        return android_open_url(payload.get("url", ""))
    if action == "open_settings":
        return open_allowed_app("settings")

    return {"ok": False, "error": "unsupported_or_blocked_action", "action": action}
