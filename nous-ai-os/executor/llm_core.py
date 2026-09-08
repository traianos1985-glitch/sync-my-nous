from executor.remote_llm import ask_remote_llm

try:
    from executor.local_llm import ask_llm
except Exception:
    ask_llm = None


def ask(prompt: str):

    try:
        remote = ask_remote_llm(prompt)

        if isinstance(remote, dict) and remote.get("success"):
            return {
                "response": remote.get("response", ""),
                "mode": "remote_llm"
            }

    except Exception as e:
        print("[REMOTE LLM ERROR]", e)

    try:
        if ask_llm is not None:
            local = ask_llm(prompt)

            if isinstance(local, dict) and local.get("success"):
                return {
                    "response": local.get("response", ""),
                    "mode": "local_mock"
                }

    except Exception as e:
        print("[LOCAL LLM ERROR]", e)

    return {
        "response": "Δεν υπάρχει διαθέσιμο LLM αυτή τη στιγμή.",
        "mode": "offline"
    }
