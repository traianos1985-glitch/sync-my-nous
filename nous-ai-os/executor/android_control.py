import subprocess
import time

from executor.android_sense import sense
from executor.notifications import notify
from executor.memory import save


def _cmd(command):
    try:
        p = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=15,
        )
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "stdout": p.stdout[-2000:],
            "stderr": p.stderr[-2000:],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def android_status():
    return {
        "sense": sense(),
        "time": time.time(),
    }


def android_notify(title="ΝΟΥΣ AI", message="Ο ΝΟΥΣ είναι ενεργός"):
    result = notify(str(title), str(message))
    save({"event": "android_notify", "title": title, "message": message})
    return {
        "sent": True,
        "result": result,
    }


def android_safe_commands():
    return {
        "available": [
            "android_status",
            "android_notify",
        ],
        "blocked": [
            "open apps",
            "tap screen",
            "send messages",
            "delete files",
            "dangerous automation",
        ],
        "note": "Android control είναι σε safe mode. Πρώτα μόνο status/notifications."
    }


def android_open_url(url):
    u = str(url).strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return {"ok": False, "error": "only_http_https_allowed"}

    result = _cmd(f'am start -a android.intent.action.VIEW -d "{u}"')
    save({"event": "android_open_url", "url": u, "ok": result.get("ok")})
    return result
