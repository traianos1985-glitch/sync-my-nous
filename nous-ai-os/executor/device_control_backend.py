import os
import time

from executor.code_assistant import run_cmd


def _ok(cmd):
    r = run_cmd(cmd)
    return bool(r.get("ok")), r


def device_control_status():
    shizuku_ok, shizuku_raw = _ok("pm list packages | grep shizuku")
    accessibility_ok, accessibility_raw = _ok("settings get secure enabled_accessibility_services")
    adb_ok, adb_raw = _ok("command -v adb")
    am_ok = os.path.exists("/system/bin/am") or os.path.exists("/data/data/com.termux/files/usr/bin/am")
    input_exists = os.path.exists("/system/bin/input")

    input_test = run_cmd("/system/bin/input keyevent 4") if input_exists else {"ok": False, "error": "input_missing"}

    return {
        "time": time.time(),
        "intents": {
            "real": bool(am_ok),
            "backend": "am",
        },
        "gestures": {
            "real": bool(input_test.get("ok")),
            "binary_exists": input_exists,
            "blocked_reason": None if input_test.get("ok") else "INJECT_EVENTS permission required",
            "backend_required": "shizuku_or_accessibility_companion_or_adb_shell",
            "test": input_test,
        },
        "shizuku": {
            "installed": shizuku_ok,
            "raw": shizuku_raw,
        },
        "accessibility": {
            "readable_from_termux": accessibility_ok,
            "raw": accessibility_raw,
        },
        "adb": {
            "installed": adb_ok,
            "raw": adb_raw,
        },
        "recommended_next_backend": "accessibility_companion_app",
    }


def device_control_recommendation():
    status = device_control_status()

    if status["gestures"]["real"]:
        return {
            "ready": True,
            "recommendation": "gestures_available",
            "next": "enable gesture executor actions",
        }

    if not status["shizuku"]["installed"]:
        return {
            "ready": False,
            "recommendation": "install_shizuku_or_build_accessibility_companion",
            "best_path": "accessibility_companion_app",
            "why": "Termux cannot inject input events without elevated backend.",
        }

    return {
        "ready": False,
        "recommendation": "configure_shizuku_bridge",
        "best_path": "shizuku_bridge",
    }
