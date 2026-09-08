import time
from executor.operator_capability_manager import operator_capabilities
from executor.code_assistant import run_cmd
from executor.agent_journal import write_journal

def deploy_provider_status():
    caps = operator_capabilities()
    return {
        "time": time.time(),
        "ready": bool(caps["deploy_ready"]),
        "providers": {
            "vercel": caps["commands"].get("vercel"),
            "railway": caps["commands"].get("railway"),
            "render": caps["commands"].get("render"),
        },
        "install_hints": caps["install_hints"],
    }

def deploy_with_provider(provider, path="."):
    status = deploy_provider_status()

    if provider == "vercel":
        if not status["providers"]["vercel"]:
            return {"ok": False, "error": "vercel_cli_not_installed", "status": status}
        cmd = f"cd {path} && vercel --prod --yes"

    elif provider == "railway":
        if not status["providers"]["railway"]:
            return {"ok": False, "error": "railway_cli_not_installed", "status": status}
        cmd = f"cd {path} && railway up"

    else:
        return {"ok": False, "error": "provider_not_supported_or_not_configured", "status": status}

    result = run_cmd(cmd)
    output = {"ok": bool(result.get("ok")), "provider": provider, "result": result}
    write_journal("deploy_provider_run", output)
    return output
