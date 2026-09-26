import os
import subprocess
import time

import requests

from executor.memory import save

CONFIG = {
    "enabled": os.environ.get("NOUS_LOCAL_LLM", "0") == "1",
    "command": os.environ.get("NOUS_LOCAL_LLM_CMD", ""),
    "base_url": os.environ.get("NOUS_LOCAL_LLM_URL", "http://127.0.0.1:11434"),
    # Qwen is the coding specialist; Llama is the general fallback.
    "coding_model": os.environ.get("NOUS_LOCAL_CODING_MODEL", "qwen2.5-coder:7b"),
    "general_model": os.environ.get("NOUS_LOCAL_GENERAL_MODEL", "llama3.1:8b"),
    "timeout": int(os.environ.get("NOUS_LOCAL_LLM_TIMEOUT", "120")),
}


def _ollama_request(prompt, model, timeout=None):
    response = requests.post(
        f"{CONFIG['base_url'].rstrip('/')}/api/generate",
        json={"model": model, "prompt": str(prompt), "stream": False},
        timeout=timeout or CONFIG["timeout"],
    )
    response.raise_for_status()
    data = response.json()
    text = str(data.get("response", "")).strip()
    if not text:
        raise RuntimeError("local_llm_empty_response")
    return text


def ask_ollama(prompt, purpose="general", timeout=None):
    if not CONFIG["enabled"]:
        return {"ok": False, "reason": "local_llm_not_enabled", "status": local_llm_status()}

    model = CONFIG["coding_model"] if purpose == "coding" else CONFIG["general_model"]
    try:
        text = _ollama_request(prompt, model, timeout)
        result = {"ok": True, "provider": "ollama", "model": model, "response": text}
        save({"event": "local_llm_call", "provider": "ollama", "model": model, "ok": True})
        return result
    except Exception as exc:
        return {"ok": False, "provider": "ollama", "model": model, "error": str(exc)}


def local_llm_status():
    return {
        "enabled": CONFIG["enabled"],
        "command_configured": bool(CONFIG["command"]),
        "command": CONFIG["command"] if CONFIG["command"] else None,
        "base_url": CONFIG["base_url"],
        "coding_model": CONFIG["coding_model"],
        "general_model": CONFIG["general_model"],
        "time": time.time(),
    }


def ask_local(prompt, timeout=60):
    if not CONFIG["enabled"] or not CONFIG["command"]:
        return {
            "ok": False,
            "reason": "local_llm_not_configured",
            "status": local_llm_status(),
        }

    try:
        p = subprocess.run(
            CONFIG["command"],
            input=str(prompt),
            shell=True,
            text=True,
            capture_output=True,
            timeout=int(timeout),
        )

        result = {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "response": p.stdout[-8000:],
            "error": p.stderr[-4000:],
        }

        save({"event": "local_llm_call", "ok": result["ok"]})
        return result

    except Exception as e:
        return {"ok": False, "error": str(e)}
