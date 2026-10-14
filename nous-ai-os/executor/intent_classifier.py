"""LLM-powered intent classifier for NOUS (rules + LLM + clarification)."""

from __future__ import annotations

import json
import re
from typing import Any

KNOWN_INTENTS = {
    "system_status", "health_check", "missions_list", "goals_list",
    "create_mission", "create_goal", "search_web", "deep_research", "read_url",
    "memory_recall", "knowledge_query", "evolve",
    "autonomous_start", "autonomous_stop", "autonomous_status",
    "capabilities", "identity", "calculator", "list_tools", "run_safe_tool",
    "request_privileged_tool", "approve_and_run", "reject_approval", "list_approvals",
    "general_chat", "unclear",
}

CONFIDENCE_ACT = 0.72
CONFIDENCE_CLARIFY = 0.45


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _rule_based(message: str) -> dict[str, Any] | None:
    m = _norm(message)
    if not m or len(m) < 2:
        return None

    for pat in [
        r"\b(έλεγχος|ελεγχος)\s+(υγείας|υγειας|συστήματος|συστηματος)\b",
        r"\b(health\s*check|system\s*health)\b",
        r"\b(πώς|πως)\s+(είναι|ειναι)\s+(το\s+)?(σύστημα|συστημα|υγεία|υγεια)\b",
        r"\b(όλα|ολα)\s+(καλά|καλα)\b",
        r"^(status|κατάσταση|κατασταση)$",
    ]:
        if re.search(pat, m):
            if re.search(r"αυτόνομ|αυτονομ|autonomous", m):
                break
            intent = "health_check" if re.search(r"υγε|health", m) else "system_status"
            return {"intent": intent, "confidence": 0.92, "slots": {}, "clarification_question": None, "source": "rules"}

    if re.search(r"\b(αποστολές|missions)\b", m) and not re.search(r"(δημιούργ|φτιάξ|plan|κάνε)", m):
        return {"intent": "missions_list", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}
    if re.search(r"\b(στόχοι|goals)\b", m) and not re.search(r"(δημιούργ|βάλε|create)", m):
        return {"intent": "goals_list", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}

    if re.search(r"\b(τι\s+εργαλεία|list\s+tools|^tools$)\b", m):
        return {"intent": "list_tools", "confidence": 0.94, "slots": {}, "clarification_question": None, "source": "rules"}
    if re.search(r"\b(τι\s+μπορείς|τι\s+μπορεις|βοήθεια|help|capabilities)\b", m):
        return {"intent": "capabilities", "confidence": 0.92, "slots": {}, "clarification_question": None, "source": "rules"}
    if re.search(r"\b(ποιος\s+είσαι|ποιος\s+εισαι)\b", m):
        return {"intent": "identity", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}

    if re.search(r"\b(θυμάσαι|θυμασαι|recall|remember)\b", m):
        q = re.sub(r"^(?:θυμάσαι|θυμασαι|recall|remember)\s+", "", message.strip(), flags=re.I).strip(" ?!.")
        return {"intent": "memory_recall", "confidence": 0.9, "slots": {"query": q or message.strip()}, "clarification_question": None, "source": "rules"}

    mm = re.match(r"^(?:δημιούργησε|δημιουργησε|φτιάξε|φτιαξε|κάνε|κανε|plan)\s+(?:μου\s+)?(?:μία?\s+|μια\s+)?(?:αποστολή|αποστολη|mission)\s*[:\-]?\s*(.+)$", message.strip(), re.I)
    if mm:
        return {"intent": "create_mission", "confidence": 0.95, "slots": {"goal": mm.group(1).strip()}, "clarification_question": None, "source": "rules"}
    gm = re.match(r"^(?:δημιούργησε|δημιουργησε|βάλε|βαλε|create)\s+(?:στόχο|στοχο|goal)\s*[:\-]?\s*(.+)$", message.strip(), re.I)
    if gm:
        return {"intent": "create_goal", "confidence": 0.95, "slots": {"title": gm.group(1).strip()}, "clarification_question": None, "source": "rules"}
    sm = re.match(r"^(?:ψάξε|ψαξε|search)\s+(?:για\s+)?(.+)$", message.strip(), re.I)
    if sm:
        return {"intent": "search_web", "confidence": 0.93, "slots": {"query": sm.group(1).strip()}, "clarification_question": None, "source": "rules"}

    urls = re.findall(r"https?://\S+", message or "")
    if urls and re.search(r"\b(διάβασε|διαβασε|read|open)\b", m):
        return {"intent": "read_url", "confidence": 0.94, "slots": {"url": urls[0].rstrip(".,)")}, "clarification_question": None, "source": "rules"}

    if re.search(r"\b(εξέλιξη|εξελιξη|self[- ]?improve)\b", m):
        return {"intent": "evolve", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}

    if re.search(r"\b(σταμάτα|stop)\s+(την\s+)?(αυτόνομη|αυτονομη|autonomous)\b", m):
        return {"intent": "autonomous_stop", "confidence": 0.93, "slots": {}, "clarification_question": None, "source": "rules"}
    if re.search(r"\b(ξεκίνα|ξεκινα|start)\s+(την\s+)?(αυτόνομη|αυτονομη|autonomous)\b", m):
        return {"intent": "autonomous_start", "confidence": 0.93, "slots": {}, "clarification_question": None, "source": "rules"}
    if re.search(r"\b(αυτόνομη|αυτονομη|autonomous)\s+(λειτουργία|status|κατάσταση)\b", m):
        return {"intent": "autonomous_status", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}

    calc = re.match(r"^(?:υπολόγισε|υπολογισε|calculate)\s+(.+)$", message.strip(), re.I)
    if calc:
        return {"intent": "calculator", "confidence": 0.95, "slots": {"expression": calc.group(1).strip()}, "clarification_question": None, "source": "rules"}

    for pat, action, cmd in [
        (r"^git\s+status$", "git_status", "git status"),
        (r"^daily\s+brief$", "daily_brief", "daily brief"),
        (r"^sysinfo$", "sysinfo", "sysinfo"),
        (r"^schedules$", "list_schedules", "schedules"),
    ]:
        if re.search(pat, m, re.I):
            return {"intent": "run_safe_tool", "confidence": 0.93, "slots": {"action": action, "command": cmd}, "clarification_question": None, "source": "rules"}

    m_appr = re.search(r"(?:ενέκρινε|ενεκρινε|approve)\s+(?:και\s+)?(?:εκτέλεσε|εκτελεσε|run)?\s*(?:approval\s+)?([\w-]+)", message.strip(), re.I)
    if not m_appr:
        m_appr = re.search(r"(?:εκτέλεσε|εκτελεσε)\s+approval\s+([\w-]+)", message.strip(), re.I)
    if m_appr:
        return {"intent": "approve_and_run", "confidence": 0.95, "slots": {"approval_id": m_appr.group(1)}, "clarification_question": None, "source": "rules"}
    m_rej = re.search(r"(?:απέρριψε|απερριψε|reject)\s+(?:approval\s+)?([\w-]+)", message.strip(), re.I)
    if m_rej:
        return {"intent": "reject_approval", "confidence": 0.95, "slots": {"approval_id": m_rej.group(1)}, "clarification_question": None, "source": "rules"}
    if re.search(r"\b(εκκρεμείς\s+εγκρίσεις|εκκρεμεις\s+εγκρισεις|pending\s+approvals|λίστα\s+εγκρίσεων)\b", m):
        return {"intent": "list_approvals", "confidence": 0.93, "slots": {}, "clarification_question": None, "source": "rules"}

    priv_patterns = [
        (r"^(?:φτιάξε|φτιαξε|γράψε|make)\s+plugin\b\s*(.*)$", "make_plugin", "make plugin"),
        (r"^(?:τρέξε|τρεξε|run)\s+plugin\b\s*(.*)$", "run_plugin", "run plugin"),
        (r"\b(επισκευή\s+συστήματος|επισκευη\s+συστηματος|repair\s+system)\b", "repair_system", "repair system"),
        (r"\b(autonomy\s+cycle)\b", "autonomy_cycle", "autonomy cycle"),
        (r"\b(clear\s+schedules)\b", "clear_schedules", "clear schedules"),
        (r"^(?:team\s+solve)\s*(.*)$", "team_solve", "team solve"),
        (r"^(?:agent\s+solve)\s*(.*)$", "agent_solve", "agent solve"),
    ]
    for pat, action, cmd_prefix in priv_patterns:
        mm = re.search(pat, message.strip(), re.I)
        if mm:
            rest = ""
            if pat.rstrip("$").endswith("(.*)") and mm.lastindex:
                rest = (mm.group(mm.lastindex) or "").strip()
            command = f"{cmd_prefix} {rest}".strip() if rest else cmd_prefix
            return {"intent": "request_privileged_tool", "confidence": 0.92, "slots": {"action": action, "command": command}, "clarification_question": None, "source": "rules"}

    return None


_CLASSIFIER_SYSTEM = "Επιστρέφεις ΜΟΝΟ JSON intent για ΝΟΥΣ. Intents: system_status, health_check, create_mission, search_web, read_url, request_privileged_tool, approve_and_run, list_approvals, capabilities, general_chat, unclear."


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


def _llm_classify(message: str) -> dict[str, Any] | None:
    try:
        from executor.remote_llm import ask_with_turns
    except Exception:
        return None
    try:
        result = ask_with_turns([{"role": "user", "content": f"Μήνυμα:\n{message}"}], system=_CLASSIFIER_SYSTEM)
    except Exception:
        return None
    if not result or not result.get("success"):
        return None
    data = _extract_json(result.get("response") or result.get("text") or "")
    if not data:
        return None
    intent = str(data.get("intent") or "unclear").strip().lower()
    if intent not in KNOWN_INTENTS:
        intent = "unclear"
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
    except Exception:
        confidence = 0.5
    slots = data.get("slots") if isinstance(data.get("slots"), dict) else {}
    clarification = data.get("clarification_question")
    if clarification is not None:
        clarification = str(clarification).strip() or None
    return {"intent": intent, "confidence": confidence, "slots": slots, "clarification_question": clarification, "source": "llm"}


def classify_intent(message: str, use_llm: bool = True) -> dict[str, Any]:
    message = (message or "").strip()
    if not message:
        return {"intent": "unclear", "confidence": 0.0, "slots": {}, "clarification_question": "Πες μου τι θα ήθελες να κάνουμε;", "source": "fallback", "needs_clarification": True}
    ruled = _rule_based(message)
    if ruled and ruled["confidence"] >= CONFIDENCE_ACT:
        ruled["needs_clarification"] = False
        return ruled
    if use_llm:
        llm_result = _llm_classify(message)
        if llm_result:
            conf, intent, slots = llm_result["confidence"], llm_result["intent"], llm_result.get("slots") or {}
            needs, question = False, llm_result.get("clarification_question")
            if intent == "unclear" or conf < CONFIDENCE_CLARIFY:
                needs = True
            elif intent == "create_mission" and not slots.get("goal"):
                needs, question = True, question or "Τι στόχο θέλεις να έχει η αποστολή;"
            elif intent == "search_web" and not slots.get("query"):
                needs, question = True, question or "Τι να ψάξω;"
            elif conf < CONFIDENCE_ACT and intent not in ("general_chat", "capabilities", "identity", "list_tools"):
                needs = True
                question = question or f"Κατάλαβα «{intent}». Να προχωρήσω;"
            if needs and not question:
                question = "Μπορείς να το πεις λίγο πιο συγκεκριμένα;"
            llm_result["needs_clarification"] = needs
            llm_result["clarification_question"] = question if needs else None
            return llm_result
    if ruled:
        ruled["needs_clarification"] = ruled["confidence"] < CONFIDENCE_ACT
        return ruled
    return {"intent": "general_chat", "confidence": 0.5, "slots": {}, "clarification_question": None, "source": "fallback", "needs_clarification": False}


def format_clarification_response(classification: dict[str, Any]) -> dict[str, Any]:
    question = classification.get("clarification_question") or "Μπορείς να μου εξηγήσεις λίγο περισσότερο τι θέλεις;"
    return {"ok": True, "source": "intent_classifier", "mode": "clarification", "intent": classification.get("intent", "unclear"), "confidence": classification.get("confidence", 0.0), "answer": question, "response": question, "text": question, "executed": False, "needs_clarification": True}
