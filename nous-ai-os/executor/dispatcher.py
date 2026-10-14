"""Legacy dispatcher — now delegates to the unified intent + tools path."""

from __future__ import annotations

from typing import Any


def dispatch(command, context=None):
    """Route a free-text command through intent understanding and tools.

    Order:
      1) try_intent_route (chat-grade NL handlers, approvals, safe tools)
      2) tools.run_tool when an action can be inferred
      3) minimal legacy fallbacks (URL fetch / search string)
    """
    context = context if isinstance(context, dict) else {}
    text = str(command or "").strip()
    if not text:
        return {"ok": False, "error": "empty_command"}

    # 1) Unified intent path (same as chat)
    try:
        from executor.intent_chat_integration import try_intent_route

        routed = try_intent_route(text)
        if routed is not None:
            return routed
    except Exception:
        pass

    # 2) Classifier → run_tool for safe / mapped actions
    try:
        from executor.intent_classifier import classify_intent
        from executor.tools import run_tool

        classification = classify_intent(text, use_llm=False)
        intent = classification.get("intent")
        slots = classification.get("slots") or {}
        conf = float(classification.get("confidence") or 0)

        if conf >= 0.72 and intent == "run_safe_tool" and slots.get("action"):
            return run_tool(
                {"action": slots["action"]},
                {"command": slots.get("command") or text},
            )

        if conf >= 0.72 and intent == "search_web" and slots.get("query"):
            return run_tool({"action": "web_search"}, {"command": f"search {slots['query']}"})

        if conf >= 0.72 and intent == "list_tools":
            return run_tool({"action": "tool_catalog"}, {"command": "tools"})
    except Exception:
        pass

    # 3) Tiny legacy fallbacks
    lower = text.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        try:
            from executor.web_tools import fetch

            return fetch(text)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    if lower.startswith("search ") or lower.startswith("ψάξε "):
        try:
            from executor.web_tools import search

            return search(text)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    return {
        "ok": False,
        "intent": None,
        "output": "NO ACTION MATCHED",
        "hint": "Δοκίμασε φυσική γλώσσα στο chat ή «τι εργαλεία έχεις;».",
    }
