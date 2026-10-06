from executor.remote_llm import ask_remote_llm

from executor.remote_llm import ask_remote_llm


def ask(prompt: str):
    try:
        result = ask_remote_llm(prompt)
    except Exception:
        return {"response": "", "mode": "offline", "error": "llm_unavailable"}

    if result.get("success") and result.get("response"):
        return {
            "response": result["response"],
            "mode": result.get("provider", "remote_llm"),
        }

    return {
        "response": "",
        "mode": "offline",
        "error": result.get("error", "llm_unavailable"),
    }
