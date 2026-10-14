"""
Intent classification integration for the chat path.

Used by chat_brain_v3 and router so natural-language intents
(status, health, missions, search, …) work without exact phrases.
"""

from __future__ import annotations

from typing import Any

from executor.intent_classifier import classify_intent, format_clarification_response


def _handle_classified_intent(classification: dict[str, Any], message: str) -> dict[str, Any] | None:
    """Map high-confidence actionable intents to concrete answers."""
    intent = classification.get("intent")
    slots = classification.get("slots") or {}

    if intent in ("system_status", "health_check"):
        try:
            from executor.natural_chat_orchestrator import _system_status_answer
            text = _system_status_answer()
        except Exception:
            text = "Δεν μπόρεσα να διαβάσω την τρέχουσα κατάσταση του συστήματος."
        if intent == "health_check":
            try:
                from executor.project_health_snapshot import run_project_health_snapshot
                snap = run_project_health_snapshot()
                if isinstance(snap, dict) and snap.get("ok") is not False:
                    extra = snap.get("summary") or snap.get("report") or ""
                    if extra:
                        text = text + "\n\n**Έλεγχος υγείας:**\n" + str(extra)[:1200]
            except Exception:
                pass
        return {
            "ok": True,
            "source": "intent_classifier",
            "mode": intent,
            "intent": intent,
            "confidence": classification.get("confidence"),
            "answer": text,
            "response": text,
            "text": text,
            "executed": True,
        }

    if intent == "missions_list":
        try:
            from executor.natural_chat_orchestrator import _missions_answer
            text = _missions_answer()
        except Exception:
            text = "Δεν μπόρεσα να διαβάσω τις αποστολές αυτή τη στιγμή."
        return {
            "ok": True,
            "source": "intent_classifier",
            "mode": "missions_list",
            "intent": intent,
            "answer": text,
            "response": text,
            "text": text,
            "executed": True,
        }

    if intent == "goals_list":
        try:
            from executor.natural_chat_orchestrator import _goals_answer
            text = _goals_answer()
        except Exception:
            text = "Δεν μπόρεσα να διαβάσω τους στόχους αυτή τη στιγμή."
        return {
            "ok": True,
            "source": "intent_classifier",
            "mode": "goals_list",
            "intent": intent,
            "answer": text,
            "response": text,
            "text": text,
            "executed": True,
        }

    if intent == "create_mission":
        goal = (slots.get("goal") or "").strip()
        if not goal:
            return None
        return {
            "ok": True,
            "source": "intent_classifier",
            "mode": "create_mission",
            "intent": intent,
            "slots": slots,
            "answer": (
                f"Κατάλαβα ότι θέλεις αποστολή με στόχο: «{goal}». "
                f"Γράψε `/plan {goal}` για να την ξεκινήσω επίσημα, ή πες μου περισσότερες λεπτομέρειες."
            ),
            "response": f"Κατάλαβα αποστολή: {goal}",
            "text": f"Κατάλαβα αποστολή: {goal}",
            "executed": False,
            "suggested_command": f"/plan {goal}",
        }

    if intent == "create_goal":
        title = (slots.get("title") or "").strip()
        if not title:
            return None
        return {
            "ok": True,
            "source": "intent_classifier",
            "mode": "create_goal",
            "intent": intent,
            "slots": slots,
            "answer": f"Κατάλαβα νέο στόχο: «{title}». Θέλεις να τον καταχωρήσω τώρα;",
            "response": f"Κατάλαβα στόχο: {title}",
            "text": f"Κατάλαβα στόχο: {title}",
            "executed": False,
        }

    if intent == "search_web":
        query = (slots.get("query") or message).strip()
        if query:
            try:
                from executor.internet_search_engine import answer_from_web
                web = answer_from_web(query)
                text = (
                    web.get("answer")
                    if isinstance(web, dict) and web.get("answer")
                    else str((web or {}).get("results", []))[:800]
                )
            except Exception:
                text = "Δεν μπόρεσα να ολοκληρώσω την αναζήτηση."
            return {
                "ok": True,
                "source": "intent_classifier",
                "mode": "internet_search",
                "intent": intent,
                "answer": text,
                "response": text,
                "text": text,
                "executed": True,
            }

    if intent == "deep_research":
        query = (slots.get("query") or message).strip()
        try:
            from executor.deep_research_engine import deep_research
            research = deep_research(query, max_results=5)
            text = research.get("answer") or "Δεν μπόρεσα να ολοκληρώσω τη βαθιά έρευνα."
        except Exception:
            text = "Δεν μπόρεσα να ολοκληρώσω τη βαθιά έρευνα."
        return {
            "ok": True,
            "source": "intent_classifier",
            "mode": "deep_research",
            "intent": intent,
            "answer": text,
            "response": text,
            "text": text,
            "executed": True,
        }

    if intent == "capabilities":
        text = (
            "Μπορώ να σε βοηθήσω με:\n"
            "• **Φυσική συζήτηση** — ρώτα με ό,τι θέλεις στα ελληνικά\n"
            "• **Κώδικα** — ανάλυση, debug, βελτίωση\n"
            "• **Αναζήτηση internet** — πες «ψάξε για...»\n"
            "• **Έγγραφα** — ανέβασε PDF/Word και ρώτα γι' αυτό\n"
            "• **Μνήμη** — θυμάμαι τις συνομιλίες μας\n"
            "• **Αποστολές** — γράψε /plan <στόχος>\n"
            "• **Κατάσταση** — πες «κατάσταση» ή «έλεγχος υγείας»"
        )
        return {
            "ok": True,
            "source": "intent_classifier",
            "mode": "capabilities",
            "intent": intent,
            "answer": text,
            "response": text,
            "text": text,
            "executed": True,
        }

    return None


def try_intent_route(message: str) -> dict[str, Any] | None:
    """
    Classify message. Return a chat response dict when we should short-circuit,
    or None to continue with the normal chat_brain flow.
    """
    try:
        classification = classify_intent(message, use_llm=True)
        if classification.get("needs_clarification"):
            return format_clarification_response(classification)
        if (
            classification.get("confidence", 0) >= 0.72
            and classification.get("intent") not in ("general_chat", "unclear")
        ):
            handled = _handle_classified_intent(classification, message)
            if handled is not None:
                return handled
    except Exception:
        pass
    return None
