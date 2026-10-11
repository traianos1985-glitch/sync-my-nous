import re
import subprocess
import time
from urllib.parse import urlsplit

from executor.android_sense import sense
from executor.notifications import notify
from executor.memory import save


_INVALID_URL_CHARS = re.compile(r"[\x00-\x20\x7f\"'\\]")


def _cmd(command):
    """Run an argument vector without invoking a shell."""
    try:
        p = subprocess.run(
            command,
            shell=False,
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


def _validated_http_url(value):
    if not isinstance(value, str):
        return None
    url = value.strip()
    if not url or _INVALID_URL_CHARS.search(url):
        return None
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return None
        # Do not allow embedded credentials or malformed ports.
        if parsed.username is not None or parsed.password is not None:
            return None
        _ = parsed.port
    except ValueError:
        return None
    return url


def android_open_url(url):
    u = _validated_http_url(url)
    if not u:
        return {"ok": False, "error": "invalid_http_https_url"}

    result = _cmd([
        "am", "start", "-a", "android.intent.action.VIEW", "-d", u
    ])
    save({"event": "android_open_url", "url": u, "ok": result.get("ok")})
    return result
