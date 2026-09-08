import time
from executor.guardian_policy import check_action
from executor.browser_automation import browser_search, browser_read
from executor.android_actions_v2 import run_android_action
from executor.web_deploy_manager import register_local_deploy
from executor.git_workflow import git_safe_checkpoint
from executor.agent_journal import write_journal

def complex_action_status():
    return {
        "allowed_steps": ["browser_search", "browser_read", "android_status", "android_notify", "android_open_url", "deploy_local_app", "git_checkpoint"],
        "blocked": ["unrestricted_shell", "payments", "messages", "delete_files"],
        "time": time.time(),
    }

def run_complex_action(steps):
    if not isinstance(steps, list):
        return {"ok": False, "error": "steps_must_be_list"}

    results = []

    for step in steps:
        name = step.get("action")
        payload = step.get("payload", {})

        if name == "browser_search":
            res = browser_search(payload.get("query", ""))
        elif name == "browser_read":
            res = browser_read(payload.get("url", ""))
        elif name == "android_status":
            res = run_android_action("status", payload)
        elif name == "android_notify":
            policy = check_action("android_notify")
            res = run_android_action("notify", payload) if policy.get("allowed") else {"ok": False, "policy": policy}
        elif name == "android_open_url":
            policy = check_action("android_open_url")
            res = run_android_action("open_url", payload) if policy.get("allowed") else {"ok": False, "policy": policy}
        elif name == "deploy_local_app":
            res = register_local_deploy(payload.get("app", ""))
        elif name == "git_checkpoint":
            res = git_safe_checkpoint(payload.get("message", "NOUS checkpoint"))
        else:
            res = {"ok": False, "error": "unknown_or_blocked_step", "action": name}

        results.append({"step": step, "result": res})

        if isinstance(res, dict) and res.get("ok") is False:
            output = {"ok": False, "stopped_at": name, "results": results}
            write_journal("complex_action_failed", output)
            return output

    output = {"ok": True, "results": results, "time": time.time()}
    write_journal("complex_action_completed", output)
    return output
