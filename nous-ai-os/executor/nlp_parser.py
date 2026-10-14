"""Natural-language command parser.

Unified with the intent classifier: prefers structured intent routing,
falls back to legacy slash-command mapping for backward compatibility.
"""

from __future__ import annotations


def normalize(text: str) -> str:
    return str(text or "").strip().lower()


_INTENT_TO_COMMAND = {
    "system_status": "/status",
    "health_check": "/status",
    "autonomous_status": "/autonomous-status",
    "autonomous_start": "/autonomous-start",
    "autonomous_stop": "/autonomous-stop",
    "evolve": "/evolve",
    "memory_recall": "/memory",
}


def parse_natural_command(command: str):
    """Return a slash command string, or the original command if unmatched."""
    raw = str(command or "").strip()
    if not raw:
        return command

    try:
        from executor.intent_classifier import classify_intent

        classification = classify_intent(raw, use_llm=False)
        intent = classification.get("intent")
        slots = classification.get("slots") or {}
        conf = float(classification.get("confidence") or 0)

        if conf >= 0.72 and intent in _INTENT_TO_COMMAND:
            return _INTENT_TO_COMMAND[intent]

        if conf >= 0.72 and intent == "search_web" and slots.get("query"):
            return f"/search {slots['query']}"

        if conf >= 0.72 and intent == "create_mission" and slots.get("goal"):
            return f"/plan {slots['goal']}"

        if conf >= 0.72 and intent == "request_privileged_tool":
            action = slots.get("action") or ""
            cmd = slots.get("command") or action
            return f"/tool-approval {cmd}".strip()

        if conf >= 0.72 and intent == "run_safe_tool":
            return slots.get("command") or slots.get("action") or raw
    except Exception:
        pass

    return _legacy_parse(normalize(raw), raw)


def _legacy_parse(cmd: str, original: str) -> str:
    if "κατάσταση αυτόνομης λειτουργίας" in cmd or "autonomous status" in cmd:
        return "/autonomous-status"

    if (
        "ποια είναι η κατάσταση του συστήματος" in cmd
        or "κατάσταση συστήματος" in cmd
        or cmd == "status"
        or cmd == "κατάσταση"
    ):
        return "/status"

    if "μνήμη" in cmd:
        return "/memory"

    if "αυτόνομη εξέλιξη" in cmd or "autonomous evolve" in cmd:
        return "/autonomous-evolve"

    if "ξεκίνα αυτόνομη λειτουργία" in cmd:
        return "/autonomous-start"

    if "σταμάτα αυτόνομη λειτουργία" in cmd:
        return "/autonomous-stop"

    if "κάνε εξέλιξη" in cmd or cmd == "evolve" or cmd == "εξέλιξη":
        return "/evolve"

    if "γράψε plugin" in cmd:
        goal = original.replace("γράψε plugin", "").strip()
        return f"/real-evolve {goal}".strip()

    if "φτιάξε plugin" in cmd:
        goal = original.replace("φτιάξε plugin", "").strip()
        return f"/real-evolve {goal}".strip()

    if "create plugin" in cmd:
        goal = original.replace("create plugin", "").strip()
        return f"/real-evolve {goal}".strip()

    if cmd.startswith("ψάξε "):
        query = original.split(" ", 1)[1]
        return f"/search {query}"

    if cmd.startswith("search "):
        query = original.split(" ", 1)[1]
        return f"/search {query}"

    return original
