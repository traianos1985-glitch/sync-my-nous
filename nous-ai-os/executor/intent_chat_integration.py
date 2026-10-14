"""
Intent classification integration for the chat path.

Used by chat_brain_v3 and router so natural-language intents
(status, health, missions, search, …) work without exact phrases.

Handlers execute real actions where safe (create mission/goal, memory recall).
"""

from __future__ import annotations

from typing import Any

from executor.intent_classifier import classify_intent, format_clarification_response


def _ok_response(
    text: str,
    *,
    intent: str,
    mode: str | None = None,
    executed: bool = True,
    confidence: float | None = None,
    slots: dict | None = None,
    **extra: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": True,
        "source": "intent_classifier",
        "mode": mode or intent,
        "intent": intent,
        "answer": text,
        "response": text,
        "text": text,
        "human_answer": text,
        "executed": executed,
    }
    if confidence is not None:
        out["confidence"] = confidence
    if slots is not None:
        out["slots"] = slots
    out.update(extra)
    return out


def _handle_classified_intent(classification: dict[str, Any], message: str) -> dict[str, Any] | None:
    """Map high-confidence actionable intents to concrete answers / side effects."""
    intent = classification.get("intent")
    slots = classification.get("slots") or {}
    confidence = classification.get("confidence")

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
        return _ok_response(text, intent=intent, confidence=confidence)

    if intent == "missions_list":
        try:
            from executor.natural_chat_orchestrator import _missions_answer

            text = _missions_answer()
        except Exception:
            text = "Δεν μπόρεσα να διαβάσω τις αποστολές αυτή τη στιγμή."
        return _ok_response(text, intent=intent, confidence=confidence)

    if intent == "goals_list":
        try:
            from executor.natural_chat_orchestrator import _goals_answer

            text = _goals_answer()
        except Exception:
            text = "Δεν μπόρεσα να διαβάσω τους στόχους αυτή τη στιγμή."
        return _ok_response(text, intent=intent, confidence=confidence)

    # --- Real create mission (no /plan required) ---
    if intent == "create_mission":
        goal = (slots.get("goal") or "").strip()
        if not goal:
            return None
        try:
            from executor.mission_system import create_mission

            mission = create_mission(goal, description=f"Δημιουργήθηκε από φυσική γλώσσα: {message[:200]}")
        except Exception as exc:
            return _ok_response(
                f"Δεν μπόρεσα να δημιουργήσω την αποστολή: {exc}",
                intent=intent,
                executed=False,
                confidence=confidence,
                slots=slots,
                ok=False,
            )
        if not isinstance(mission, dict) or not mission.get("id"):
            err = mission.get("error") if isinstance(mission, dict) else "unknown"
            return _ok_response(
                f"Δεν μπόρεσα να δημιουργήσω την αποστολή ({err}).",
                intent=intent,
                executed=False,
                confidence=confidence,
                slots=slots,
                ok=False,
            )
        mid = mission.get("id")
        title = mission.get("title") or goal
        text = (
            f"✅ Δημιούργησα την αποστολή **{title}** (id: `{mid}`).\n\n"
            f"Είναι ενεργή. Μπορείς να δεις τις αποστολές λέγοντας «αποστολές» "
            f"ή να την προχωρήσεις από το dashboard."
        )
        return _ok_response(
            text,
            intent=intent,
            confidence=confidence,
            slots=slots,
            mission_id=str(mid),
            mission=mission,
        )

    # --- Real create goal ---
    if intent == "create_goal":
        title = (slots.get("title") or "").strip()
        if not title:
            return None
        try:
            from executor.goal_system import create_goal

            goal = create_goal(title)
        except Exception as exc:
            return _ok_response(
                f"Δεν μπόρεσα να αποθηκεύσω τον στόχο: {exc}",
                intent=intent,
                executed=False,
                confidence=confidence,
                slots=slots,
                ok=False,
            )
        if not isinstance(goal, dict) or not goal.get("id"):
            return _ok_response(
                "Δεν μπόρεσα να επιβεβαιώσω την αποθήκευση του στόχου.",
                intent=intent,
                executed=False,
                confidence=confidence,
                slots=slots,
                ok=False,
            )
        text = f"✅ Καταχωρίστηκε ο στόχος **{goal.get('title', title)}** (id: `{goal.get('id')}`)."
        return _ok_response(
            text,
            intent=intent,
            confidence=confidence,
            slots=slots,
            goal_id=str(goal.get("id")),
            goal=goal,
        )

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
            return _ok_response(text, intent=intent, mode="internet_search", confidence=confidence)

    if intent == "deep_research":
        query = (slots.get("query") or message).strip()
        try:
            from executor.deep_research_engine import deep_research

            research = deep_research(query, max_results=5)
            text = research.get("answer") or "Δεν μπόρεσα να ολοκληρώσω τη βαθιά έρευνα."
        except Exception:
            text = "Δεν μπόρεσα να ολοκληρώσω τη βαθιά έρευνα."
        return _ok_response(text, intent=intent, confidence=confidence)

    # --- Memory recall ---
    if intent == "memory_recall":
        query = (slots.get("query") or message or "").strip()
        # Strip common Greek/English recall prefixes so the search is cleaner
        import re

        cleaned = re.sub(
            r"^(?:θυμάσαι|θυμασαι|θυμήσου|θυμησου|recall|remember)\s+(?:ότι|οτι|για|το|τα|αν)?\s*",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip(" ?!.·")
        try:
            from executor.long_memory import recall

            text = recall(cleaned or query)
        except Exception:
            text = "Δεν μπόρεσα να ψάξω στη μνήμη αυτή τη στιγμή."
        return _ok_response(text, intent=intent, confidence=confidence, slots={"query": cleaned or query})

    if intent == "capabilities":
        text = (
            "Μπορώ να σε βοηθήσω με:\n"
            "• **Φυσική συζήτηση** — ρώτα με ό,τι θέλεις στα ελληνικά\n"
            "• **Κώδικα** — ανάλυση, debug, βελτίωση\n"
            "• **Αναζήτηση internet** — πες «ψάξε για...»\n"
            "• **Έγγραφα** — ανέβασε PDF/Word και ρώτα γι' αυτό\n"
            "• **Μνήμη** — πες «θυμάσαι …»\n"
            "• **Αποστολές** — πες «φτιάξε αποστολή …» (χωρίς /plan)\n"
            "• **Στόχοι** — πες «δημιούργησε στόχο …»\n"
            "• **Κατάσταση** — πες «κατάσταση» ή «έλεγχος υγείας»"
        )
        return _ok_response(text, intent=intent, confidence=confidence)

    if intent == "identity":
        text = (
            "Εμένα με λένε ΝΟΥΣ. Είμαι ο προσωπικός σου AI βοηθός για συζήτηση, "
            "κώδικα, έρευνα, έγγραφα, μνήμη και αποστολές. Ρώτα με ό,τι θέλεις στα ελληνικά!"
        )
        return _ok_response(text, intent=intent, confidence=confidence)

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
