"""Intent classification integration for the chat path."""

from __future__ import annotations

import re
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
    ok: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": ok,
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


def _external_call_allowed(action: str) -> tuple[bool, str]:
    """Fail closed when the external-call policy cannot be evaluated."""
    try:
        from executor.capability_awareness import allow_external_call

        allowed, message = allow_external_call(action)
        if not allowed:
            return False, str(message or "Η εξωτερική κλήση δεν επιτρέπεται αυτή τη στιγμή.")
        return True, ""
    except Exception:
        return False, "Δεν ήταν δυνατός ο έλεγχος της πολιτικής εξωτερικών κλήσεων· η ενέργεια μπλοκαρίστηκε."


def _handle_classified_intent(classification: dict[str, Any], message: str) -> dict[str, Any] | None:
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

    if intent == "create_mission":
        goal = (slots.get("goal") or "").strip()
        if not goal:
            return None
        try:
            from executor.mission_system import create_mission

            mission = create_mission(goal, description=f"Δημιουργήθηκε από φυσική γλώσσα: {message[:200]}")
        except Exception as exc:
            return _ok_response(f"Δεν μπόρεσα να δημιουργήσω την αποστολή: {exc}", intent=intent, executed=False, confidence=confidence, slots=slots, ok=False)
        if not isinstance(mission, dict) or not mission.get("id"):
            return _ok_response("Δεν μπόρεσα να δημιουργήσω την αποστολή.", intent=intent, executed=False, confidence=confidence, slots=slots, ok=False)
        mid, title = mission.get("id"), mission.get("title") or goal
        return _ok_response(f"✅ Δημιούργησα την αποστολή **{title}** (id: `{mid}`).", intent=intent, confidence=confidence, slots=slots, mission_id=str(mid), mission=mission)

    if intent == "create_goal":
        title = (slots.get("title") or "").strip()
        if not title:
            return None
        try:
            from executor.goal_system import create_goal

            goal = create_goal(title)
        except Exception as exc:
            return _ok_response(f"Δεν μπόρεσα να αποθηκεύσω τον στόχο: {exc}", intent=intent, executed=False, confidence=confidence, slots=slots, ok=False)
        if not isinstance(goal, dict) or not goal.get("id"):
            return _ok_response("Δεν μπόρεσα να επιβεβαιώσω την αποθήκευση του στόχου.", intent=intent, executed=False, confidence=confidence, slots=slots, ok=False)
        return _ok_response(f"✅ Καταχωρίστηκε ο στόχος **{goal.get('title', title)}** (id: `{goal.get('id')}`).", intent=intent, confidence=confidence, slots=slots, goal_id=str(goal.get("id")), goal=goal)

    if intent == "search_web":
        query = (slots.get("query") or message).strip()
        if query:
            ok_rl, msg_rl = _external_call_allowed("search")
            if not ok_rl:
                return _ok_response(msg_rl, intent=intent, executed=False, confidence=confidence, ok=False)
            try:
                from executor.internet_search_engine import answer_from_web

                web = answer_from_web(query)
                text = web.get("answer") if isinstance(web, dict) and web.get("answer") else str((web or {}).get("results", []))[:800]
            except Exception as exc:
                from executor.capability_awareness import format_tool_error

                text = format_tool_error("search_web", exc)
            return _ok_response(text, intent=intent, mode="internet_search", confidence=confidence)

    if intent == "deep_research":
        query = (slots.get("query") or message).strip()
        ok_rl, msg_rl = _external_call_allowed("deep_research")
        if not ok_rl:
            return _ok_response(msg_rl, intent=intent, executed=False, confidence=confidence, ok=False)
        try:
            from executor.deep_research_engine import deep_research

            research = deep_research(query, max_results=5)
            text = research.get("answer") or "Δεν μπόρεσα να ολοκληρώσω τη βαθιά έρευνα."
        except Exception:
            text = "Δεν μπόρεσα να ολοκληρώσω τη βαθιά έρευνα."
        return _ok_response(text, intent=intent, confidence=confidence)

    if intent == "memory_recall":
        query = (slots.get("query") or message or "").strip()
        cleaned = re.sub(r"^(?:θυμάσαι|θυμασαι|θυμήσου|θυμησου|recall|remember)\s+(?:ότι|οτι|για|το|τα|αν)?\s*", "", query, flags=re.I).strip(" ?!.·")
        try:
            from executor.long_memory import recall

            text = recall(cleaned or query)
        except Exception:
            text = "Δεν μπόρεσα να ψάξω στη μνήμη αυτή τη στιγμή."
        return _ok_response(text, intent=intent, confidence=confidence, slots={"query": cleaned or query})

    if intent == "read_url":
        ok_rl, msg_rl = _external_call_allowed("url")
        if not ok_rl:
            return _ok_response(msg_rl, intent=intent, executed=False, confidence=confidence, ok=False)
        url = (slots.get("url") or "").strip()
        if not url:
            found = re.findall(r"https?://[^\s]+", message or "")
            url = found[0] if found else ""
        if not url:
            return None
        try:
            from executor.url_reader_engine import summarize_url

            result = summarize_url(url)
        except Exception as exc:
            from executor.capability_awareness import format_tool_error

            return _ok_response(format_tool_error("read_url", exc), intent=intent, executed=False, confidence=confidence, slots={"url": url}, ok=False)
        text = result.get("answer") or "Δεν μπόρεσα να διαβάσω τη σελίδα."
        return _ok_response(text, intent=intent, confidence=confidence, slots={"url": url}, ok=bool(result.get("ok")), executed=bool(result.get("ok")), url=url, title=result.get("title"))

    if intent == "evolve":
        parts = ["**Εξέλιξη / self-improvement**", ""]
        try:
            from executor.self_improvement_engine import self_improvement_status

            st = self_improvement_status()
            patches = st.get("patches") or []
            pending = [p for p in patches if isinstance(p, dict) and p.get("status") == "pending"]
            parts.append(f"• Patches: {len(patches)} (εκκρεμή: {len(pending)})")
        except Exception as exc:
            parts.append(f"• Status error: {exc}")
        parts.append("Δεν εφαρμόζω αυτόματα patches από το chat.")
        return _ok_response("\n".join(parts), intent=intent, confidence=confidence)

    if intent == "autonomous_status":
        try:
            from executor import mode as mode_mod

            on = bool(mode_mod.status().get("autonomous"))
            text = f"Η αυτόνομη λειτουργία είναι **{'ενεργή' if on else 'ανενεργή'}**."
        except Exception as exc:
            text = f"Δεν μπόρεσα να διαβάσω την αυτόνομη κατάσταση: {exc}"
        return _ok_response(text, intent=intent, confidence=confidence)

    if intent == "autonomous_start":
        try:
            from executor import mode as mode_mod

            mode_mod.enable()
            return _ok_response("✅ Ενεργοποίησα την αυτόνομη λειτουργία.", intent=intent, confidence=confidence)
        except Exception as exc:
            return _ok_response(f"Αποτυχία: {exc}", intent=intent, executed=False, confidence=confidence, ok=False)

    if intent == "autonomous_stop":
        try:
            from executor import mode as mode_mod

            if hasattr(mode_mod, "disable"):
                mode_mod.disable()
            else:
                mode_mod.MODE["autonomous"] = False
            return _ok_response("✅ Απενεργοποίησα την αυτόνομη λειτουργία.", intent=intent, confidence=confidence)
        except Exception as exc:
            return _ok_response(f"Αποτυχία: {exc}", intent=intent, executed=False, confidence=confidence, ok=False)

    if intent == "capabilities":
        try:
            from executor.capability_awareness import build_capabilities_text

            text = build_capabilities_text(detailed=bool(slots.get("detailed")))
        except Exception as exc:
            text = f"Δεν μπόρεσα να φορτώσω τις δυνατότητες: {exc}"
        return _ok_response(text, intent=intent, confidence=confidence)

    if intent == "list_tools":
        try:
            from executor.capability_awareness import build_tools_list_text

            text = build_tools_list_text(category=(slots.get("category") or "").strip() or None)
        except Exception as exc:
            text = f"Δεν μπόρεσα να φορτώσω εργαλεία: {exc}"
        return _ok_response(text, intent=intent, confidence=confidence)

    if intent == "calculator":
        expr = (slots.get("expression") or message or "").strip()
        expr = re.sub(r"^(?:υπολόγισε|υπολογισε|calculate)\s+", "", expr, flags=re.I).strip()
        if not expr:
            return None
        from executor.capability_awareness import run_safe_tool

        out = run_safe_tool("calculate", command=f"calculate {expr}")
        text = out.get("answer") or str(out)
        try:
            import json as _json

            parsed = out.get("result")
            if isinstance(parsed, dict) and "result" in parsed:
                text = f"**{parsed.get('expression', expr)}** = **{parsed.get('result')}**"
            elif isinstance(text, str) and text.strip().startswith("{"):
                data = _json.loads(text)
                if isinstance(data, dict) and "result" in data:
                    text = f"**{data.get('expression', expr)}** = **{data.get('result')}**"
        except Exception:
            pass
        return _ok_response(
            text,
            intent=intent,
            confidence=confidence,
            ok=bool(out.get("ok")),
            executed=bool(out.get("ok")),
        )

    if intent == "run_safe_tool":
        action = (slots.get("action") or "").strip()
        if not action:
            return None
        from executor.capability_awareness import run_safe_tool

        out = run_safe_tool(action, command=(slots.get("command") or message or action).strip())
        return _ok_response(out.get("answer") or str(out), intent=intent, confidence=confidence, ok=bool(out.get("ok")), executed=bool(out.get("ok")), tool=action)

    if intent == "request_privileged_tool":
        action = (slots.get("action") or "").strip()
        if not action:
            return None
        from executor.capability_awareness import request_privileged_tool

        out = request_privileged_tool(action, command=(slots.get("command") or message or action).strip())
        return _ok_response(out.get("answer") or str(out), intent=intent, confidence=confidence, ok=bool(out.get("ok")), executed=False, approval_required=bool(out.get("approval_required")), approval_id=out.get("approval_id"), tool=action)

    if intent == "approve_and_run":
        aid = str(slots.get("approval_id") or "").strip()
        if not aid:
            return None
        from executor.capability_awareness import approve_and_execute

        out = approve_and_execute(aid)
        return _ok_response(out.get("answer") or str(out), intent=intent, confidence=confidence, ok=bool(out.get("ok")), executed=bool(out.get("ok")), approval_id=aid)

    if intent == "reject_approval":
        aid = str(slots.get("approval_id") or "").strip()
        if not aid:
            return None
        from executor.capability_awareness import reject_approval_request

        out = reject_approval_request(aid)
        return _ok_response(out.get("answer") or str(out), intent=intent, confidence=confidence, ok=bool(out.get("ok")), executed=False)

    if intent == "list_approvals":
        from executor.capability_awareness import list_pending_approvals_text

        return _ok_response(list_pending_approvals_text(), intent=intent, confidence=confidence)

    if intent == "identity":
        return _ok_response(
            "Εμένα με λένε ΝΟΥΣ. Ρώτα «τι μπορείς;» ή «τι εργαλεία έχεις;». "
            "Για 🔒: αίτημα έγκρισης, μετά «ενέκρινε και εκτέλεσε <id>».",
            intent=intent,
            confidence=confidence,
        )

    return None


def try_intent_route(message: str) -> dict[str, Any] | None:
    try:
        classification = classify_intent(message, use_llm=True)
        try:
            from executor.session_context import remember_classification

            remember_classification(classification, message)
        except Exception:
            pass
        if classification.get("needs_clarification"):
            return format_clarification_response(classification)
        if classification.get("confidence", 0) >= 0.72 and classification.get("intent") not in ("general_chat", "unclear"):
            handled = _handle_classified_intent(classification, message)
            if handled is not None:
                return handled
    except Exception:
        pass
    return None
