import time
from executor.code_assistant import run_cmd, code_health
from executor.reality_gate import reality_status
from executor.git_workflow import git_workflow_status, git_safe_checkpoint
from executor.vercel_deploy_integration import vercel_status, vercel_deploy
from executor.companion_bridge import companion_status, companion_home, companion_back, companion_ui_tree
from executor.agent_journal import write_journal


def ops_status():
    return {
        "time": time.time(),
        "safe_actions": [
            "git_status",
            "code_health",
            "reality_status",
            "vercel_status",
            "companion_status",
            "companion_home",
            "companion_back",
            "companion_ui_tree",
            "checkpoint",
            "deploy_vercel_test_app",
            "full_validation",
        ],
        "blocked": [
            "arbitrary_shell",
            "delete_files",
            "send_messages",
            "payments",
            "unapproved_tap",
        ],
    }


def ops_git_status():
    return git_workflow_status()


def ops_code_health():
    return code_health()


def ops_reality_status():
    return reality_status()


def ops_vercel_status():
    return vercel_status()


def ops_companion_status():
    return companion_status()


def ops_checkpoint(message="NOUS safe checkpoint"):
    return git_safe_checkpoint(message)


def ops_deploy_vercel_test_app():
    return vercel_deploy("vercel_test_app", True)


def ops_full_validation():
    result = {
        "time": time.time(),
        "code_health": code_health(),
        "reality": reality_status(),
        "git": git_workflow_status(),
        "vercel": vercel_status(),
        "companion": companion_status(),
    }
    write_journal("ops_full_validation", result)
    return result


def run_ops_action(action, payload=None):
    payload = payload or {}

    if action == "git_status":
        result = ops_git_status()
    elif action == "code_health":
        result = ops_code_health()
    elif action == "reality_status":
        result = ops_reality_status()
    elif action == "vercel_status":
        result = ops_vercel_status()
    elif action == "companion_status":
        result = ops_companion_status()
    elif action == "companion_home":
        result = companion_home()
    elif action == "companion_back":
        result = companion_back()
    elif action == "companion_ui_tree":
        result = companion_ui_tree()
    elif action == "checkpoint":
        result = ops_checkpoint(payload.get("message", "NOUS safe checkpoint"))
    elif action == "deploy_vercel_test_app":
        result = ops_deploy_vercel_test_app()
    elif action == "full_validation":
        result = ops_full_validation()
    else:
        return {
            "ok": False,
            "error": "unknown_or_blocked_ops_action",
            "action": action,
            "allowed": ops_status()["safe_actions"],
        }

    output = {
        "ok": True,
        "action": action,
        "result": result,
        "time": time.time(),
    }

    write_journal("ops_action_executed", output)
    return output
