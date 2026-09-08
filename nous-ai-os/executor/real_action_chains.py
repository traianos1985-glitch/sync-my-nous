import time

from executor.real_action_gate import run_real_action, available_real_actions
from executor.agent_journal import write_journal


def run_real_chain(steps):
    if not isinstance(steps, list):
        return {"ok": False, "error": "steps_must_be_list"}

    results = []

    for step in steps:
        action = step.get("action")
        payload = step.get("payload", {})

        result = run_real_action(action, payload)
        results.append({"action": action, "payload": payload, "result": result})

        if not result.get("ok"):
            output = {
                "ok": False,
                "stopped_at": action,
                "results": results,
                "available": available_real_actions(),
                "time": time.time(),
            }
            write_journal("real_chain_stopped", output)
            return output

    output = {
        "ok": True,
        "results": results,
        "time": time.time(),
    }

    write_journal("real_chain_completed", output)
    return output


def real_chain_status():
    return {
        "available_actions": available_real_actions(),
        "examples": [
            ["internet_search", "browser_read"],
            ["code_health", "git_status"],
            ["android_notify", "android_open_url"],
        ],
        "time": time.time(),
    }
