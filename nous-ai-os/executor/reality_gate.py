import time

from executor.research_browser_agent import research_query, read_url
from executor.android_operator import operator_capabilities
from executor.code_assistant import code_health, run_cmd
from executor.app_builder import list_apps


def check_internet():
    try:
        r = research_query("Python Flask", learn=False)
        ok = bool(r.get("result", {}).get("results"))
        return {"real": ok, "details": r.get("result")}
    except Exception as e:
        return {"real": False, "error": str(e)}


def check_browser_read():
    try:
        r = read_url("https://example.com", learn=False)
        content = str(r.get("content", ""))
        return {"real": bool(content), "details": content[:300]}
    except Exception as e:
        return {"real": False, "error": str(e)}


def check_android():
    caps = operator_capabilities()
    return {
        "real_intents": bool(caps.get("am_exists")),
        "real_gesture_binary": bool(caps.get("real_gestures_binary")),
        "real_gestures": bool(caps.get("real_gestures_permission")),
        "details": caps,
    }


def check_git():
    r = run_cmd("git status --short")
    return {"real": bool(r.get("ok")), "details": r}


def check_code():
    h = code_health()
    broken = [k for k, v in h.get("compile", {}).items() if not v.get("ok")]
    return {"real": len(broken) == 0, "broken": broken}


def check_app_factory():
    try:
        apps = list_apps()
        return {"real": True, "apps": apps}
    except Exception as e:
        return {"real": False, "error": str(e)}


def reality_status():
    internet = check_internet()
    browser_read = check_browser_read()
    android = check_android()
    git = check_git()
    code = check_code()
    app_factory = check_app_factory()
    checks = {
        "internet_search": internet.get("real"),
        "browser_read": browser_read.get("real"),
        "android_intents": android.get("real_intents"),
        "git_status": git.get("real"),
        "code_compile": code.get("real"),
        "app_factory": app_factory.get("real"),
    }
    return {
        "time": time.time(),
        "internet": internet,
        "browser_read": browser_read,
        "android": android,
        "git": git,
        "code": code,
        "app_factory": app_factory,
        "summary": {
            "real_now": [name for name, ok in checks.items() if ok],
            "unavailable_now": [name for name, ok in checks.items() if not ok],
            "blocked_or_partial": [
                "android_tap_swipe_without_INJECT_EVENTS",
                "real_login_without_browser_driver",
                "real_hosting_deploy_without_provider_credentials",
            ],
        },
    }
