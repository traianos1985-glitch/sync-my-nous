import time

SAFE_ACTIONS = {
    "decide",
    "act",
    "learning_cycle",
    "research_query",
    "browser_read",
    "code_health",
    "app_queue",
    "android_status",
    "android_notify",
    "android_open_url",
}

BLOCKED_ACTIONS = {
    "delete_files",
    "send_sms",
    "send_email",
    "tap_screen",
    "install_apps",
    "run_shell_unrestricted",
    "modify_core_without_test",
}


def check_action(action, payload=None):
    action = str(action)
    payload = payload or {}

    if action in BLOCKED_ACTIONS:
        return {
            "allowed": False,
            "action": action,
            "reason": "blocked_by_guardian_policy",
            "time": time.time(),
        }

    if action in SAFE_ACTIONS:
        return {
            "allowed": True,
            "action": action,
            "reason": "safe_action",
            "time": time.time(),
        }

    return {
        "allowed": False,
        "action": action,
        "reason": "unknown_action_requires_review",
        "time": time.time(),
    }


def policy_status():
    return {
        "safe_actions": sorted(SAFE_ACTIONS),
        "blocked_actions": sorted(BLOCKED_ACTIONS),
        "time": time.time(),
    }
