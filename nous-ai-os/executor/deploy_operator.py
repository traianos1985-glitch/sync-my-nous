import os, time
from executor.code_assistant import run_cmd
from executor.agent_journal import write_journal
from executor.operator_approval import request_approval, is_approved

def deploy_operator_status():
    return {
        "mode": "provider_adapter",
        "supported": ["local", "git_push"],
        "future": ["render", "railway", "vercel", "fly_io"],
        "time": time.time(),
    }

def prepare_real_deploy(provider, app_name, approval_id=None):
    payload = {"provider": provider, "app": app_name}
    if provider not in ["local", "git_push"]:
        return {"ok": False, "error": "provider_not_configured_yet", "supported_now": ["local", "git_push"]}
    if not approval_id:
        return request_approval("real_deploy", payload, "deployment requires approval")
    if not is_approved(approval_id):
        return {"ok": False, "error": "approval_required", "approval_id": approval_id}

    if provider == "git_push":
        result = {
            "status": run_cmd("git status --short"),
            "push": run_cmd("git push"),
        }
    else:
        result = {"ok": True, "message": "local deploy already served by /apps/<name>/"}

    write_journal("real_deploy_executed", {"payload": payload, "result": result})
    return {"ok": True, "provider": provider, "result": result}
