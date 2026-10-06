def chat_fallback(text, context=None):
    return {
        "ok": False,
        "error": "llm_unavailable",
        "mode": "offline",
        "response": "Δεν είναι διαθέσιμο αυτή τη στιγμή κανένα AI μοντέλο για να απαντήσω.",
    }
