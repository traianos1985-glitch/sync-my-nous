import os
import platform
import time

from executor.code_assistant import run_cmd
from executor.operator_capability_manager import operator_capabilities


def backend_environment():
    return {
        "time": time.time(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "is_android_termux": os.path.exists("/data/data/com.termux"),
        "caps": operator_capabilities(),
    }


def browser_backend_status():
    env = backend_environment()
    caps = env["caps"]

    playwright_installed = caps["commands"].get("playwright", False)

    if env["is_android_termux"]:
        return {
            "local_browser_driver": False,
            "playwright_installed": playwright_installed,
            "reason": "playwright_unsupported_on_android_termux",
            "required_backend": "remote_browser_worker_or_companion_app",
            "real_available_now": False,
            "env": env,
        }

    return {
        "local_browser_driver": bool(caps["browser_driver_ready"]),
        "playwright_installed": playwright_installed,
        "reason": None if caps["browser_driver_ready"] else "browser_driver_not_installed",
        "required_backend": None if caps["browser_driver_ready"] else "install_playwright_or_browser",
        "real_available_now": bool(caps["browser_driver_ready"]),
        "env": env,
    }


def android_backend_status():
    input_test = run_cmd("/system/bin/input keyevent 4")
    return {
        "am_available": os.path.exists("/system/bin/am"),
        "input_binary_available": os.path.exists("/system/bin/input"),
        "input_permission": bool(input_test.get("ok")),
        "input_test": input_test,
        "required_backend_for_gestures": None if input_test.get("ok") else "shizuku_root_adb_or_accessibility_companion",
        "real_gestures_now": bool(input_test.get("ok")),
        "real_intents_now": os.path.exists("/system/bin/am"),
        "time": time.time(),
    }


def deployment_backend_status():
    caps = operator_capabilities()
    return {
        "vercel_cli": caps["commands"].get("vercel", False),
        "railway_cli": caps["commands"].get("railway", False),
        "render_cli": caps["commands"].get("render", False),
        "real_deploy_now": bool(caps["deploy_ready"]),
        "required": "install_and_login_provider_cli",
        "install_hints": caps["install_hints"],
        "time": time.time(),
    }


def operator_backend_status():
    return {
        "browser": browser_backend_status(),
        "android": android_backend_status(),
        "deployment": deployment_backend_status(),
        "summary": {
            "real_now": [
                "internet_search",
                "browser_http_read",
                "android_intents",
                "git",
                "code_compile",
                "app_factory_local",
            ],
            "requires_backend": [
                "browser_clicks_forms_login",
                "android_tap_swipe",
                "real_cloud_deploy",
            ],
        },
        "time": time.time(),
    }
