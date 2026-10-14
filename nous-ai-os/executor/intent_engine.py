"""
Compatibility layer + structured intent parsing for NOUS.

Prefers the new LLM/rule hybrid classifier (intent_classifier.py).
Keeps the old simple API used by pipeline.py.
"""

from __future__ import annotations

from typing import Any

from executor.intent_classifier import classify_intent


def parse_intent(text: str) -> dict[str, Any]:
    """
    Legacy-compatible parse_intent used by pipeline.py.

    Returns a dict with at least:
      - intent
      - action   (mapped for older consumers)
    """
    classification = classify_intent(text, use_llm=True)

    intent = classification.get("intent", "chat")
    slots = classification.get("slots") or {}

    # Map modern intents → legacy "action" values expected by pipeline / older code
    action_map = {
        "system_status": "show_status",
        "health_check": "show_status",
        "evolve": "run_evolution",
        "capabilities": "llm_fallback",
        "identity": "llm_fallback",
        "general_chat": "llm_fallback",
        "unclear": "llm_fallback",
        "missions_list": "show_missions",
        "goals_list": "show_goals",
        "create_mission": "create_mission",
        "create_goal": "create_goal",
        "search_web": "search_web",
        "deep_research": "deep_research",
        "read_url": "read_url",
        "memory_recall": "memory_recall",
        "knowledge_query": "knowledge_query",
        "autonomous_start": "autonomous_start",
        "autonomous_stop": "autonomous_stop",
        "autonomous_status": "autonomous_status",
        "calculator": "calculator",
    }

    action = action_map.get(intent, "llm_fallback")

    # Slash commands still win
    if text.strip().startswith("/"):
        return {
            "intent": "command",
            "action": text.strip(),
            "classification": classification,
        }

    return {
        "intent": intent,
        "action": action,
        "slots": slots,
        "confidence": classification.get("confidence", 0.0),
        "needs_clarification": classification.get("needs_clarification", False),
        "clarification_question": classification.get("clarification_question"),
        "source": classification.get("source"),
        "classification": classification,
    }
