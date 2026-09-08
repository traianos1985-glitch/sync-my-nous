import time

from executor.reality_gate import reality_status
from executor.research_browser_agent import research_query, read_url
from executor.android_control import android_open_url, android_notify
from executor.code_assistant import code_health
from executor.git_workflow import git_workflow_status
from executor.app_factory_v2 import create_app_from_idea, app_factory_status
from executor.agent_journal import write_journal


def available_real_actions():
    r = reality_status()
    return {
        "internet_search": bool(r["internet"]["real"]),
        "browser_read": bool(r["browser_read"]["real"]),
        "android_open_url": bool(r["android"]["real_intents"]),
        "android_notify": True,
        "git_status": bool(r["git"]["real"]),
        "code_health": bool(r["code"]["real"]),
        "app_factory": bool(r["app_factory"]["real"]),
        "android_gestures": bool(r["android"]["real_gestures"]),
        "real_hosting_deploy": False,
        "browser_login": False,
        "time": time.time(),
    }


def run_real_action(action, payload=None):
    payload = payload or {}
    allowed = available_real_actions()

    if action not in allowed:
        return {"ok": False, "error": "unknown_action", "available": allowed}

    if not allowed[action]:
        return {"ok": False, "error": "action_not_real_available", "action": action, "available": allowed}

    if action == "internet_search":
        result = research_query(payload.get("query", ""), learn=bool(payload.get("learn", False)))

    elif action == "browser_read":
        result = read_url(payload.get("url", ""), learn=bool(payload.get("learn", False)))

    elif action == "android_open_url":
        result = android_open_url(payload.get("url", ""))

    elif action == "android_notify":
        result = android_notify(payload.get("title", "ΝΟΥΣ AI"), payload.get("message", "Ο ΝΟΥΣ είναι ενεργός"))

    elif action == "git_status":
        result = git_workflow_status()

    elif action == "code_health":
        result = code_health()

    elif action == "app_factory":
        result = create_app_from_idea(payload.get("idea", ""))

    else:
        result = {"ok": False, "error": "not_implemented"}

    output = {
        "ok": True,
        "action": action,
        "payload": payload,
        "result": result,
        "time": time.time(),
    }

    write_journal("real_action_executed", output)
    return output


def real_actions_status():
    return {
        "available": available_real_actions(),
        "note": "Only actions proven by reality_gate are executable.",
        "time": time.time(),
    }
