def parse_intent(text: str):

    text = text.lower().strip()

    if "τι κάνεις" in text or "status" in text:
        return {
            "intent": "status",
            "action": "show_status"
        }

    if "evolve" in text or "εξέλιξη" in text:
        return {
            "intent": "evolve",
            "action": "run_evolution"
        }

    if "plugin" in text:
        return {
            "intent": "plugin",
            "action": "manage_plugins"
        }

    if text.startswith("/"):
        return {
            "intent": "command",
            "action": text
        }

    return {
        "intent": "chat",
        "action": "llm_fallback"
    }
