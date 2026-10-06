def chat_fallback(text, context):
    return {
        "intent": "chat",
        "ok": False,
        "error": "llm_unavailable",
        "response": "Δεν είναι διαθέσιμο αυτή τη στιγμή κανένα AI μοντέλο για να απαντήσω.",
        "mode": "offline",
    }
