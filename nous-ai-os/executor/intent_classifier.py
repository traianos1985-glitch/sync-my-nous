"""
LLM-powered intent classifier for NOUS.

Understands natural Greek (and mixed) language, extracts structured intent + slots,
and asks clarifying questions when confidence is low or required info is missing.

Hybrid design:
  1. Fast rule-based path for very clear / high-precision phrases
  2. LLM classification (Gemini / Ollama) for everything else
  3. Clarification loop when ambiguous
"""

from __future__ import annotations

import json
import re
from typing import Any

KNOWN_INTENTS = {
    "system_status",
    "health_check",
    "missions_list",
    "goals_list",
    "create_mission",
    "create_goal",
    "search_web",
    "deep_research",
    "read_url",
    "memory_recall",
    "knowledge_query",
    "evolve",
    "autonomous_start",
    "autonomous_stop",
    "autonomous_status",
    "capabilities",
    "identity",
    "calculator",
    "general_chat",
    "unclear",
}

CONFIDENCE_ACT = 0.72
CONFIDENCE_CLARIFY = 0.45


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _rule_based(message: str) -> dict[str, Any] | None:
    m = _norm(message)
    if not m or len(m) < 2:
        return None

    health_patterns = [
        r"\b(έλεγχος|ελεγχος)\s+(υγείας|υγειας|συστήματος|συστηματος)\b",
        r"\b(health\s*check|project\s*health|system\s*health)\b",
        r"\b(πώς|πως)\s+(είναι|ειναι)\s+(το\s+)?(σύστημα|συστημα|υγεία|υγεια)\b",
        r"\b(όλα|ολα)\s+(καλά|καλα|εντάξει|ενταξει)\b",
        r"\b(τι\s+τρέχει|τι\s+τρεχει|τι\s+γίνεται|τι\s+γινεται)\b",
        r"\b(κατάσταση|κατασταση)\s+(συστήματος|συστηματος|νους|nous)?\b",
        r"^(status|κατάσταση|κατασταση)$",
    ]
    for pat in health_patterns:
        if re.search(pat, m):
            if re.search(r"αυτόνομ|αυτονομ|autonomous", m):
                break
            intent = "health_check" if re.search(r"υγε|health", m) else "system_status"
            return {
                "intent": intent,
                "confidence": 0.92,
                "slots": {},
                "clarification_question": None,
                "source": "rules",
            }

    if re.search(r"\b(αποστολές|αποστολες|missions)\b", m) and not re.search(r"(δημιούργ|δημιουργ|φτιάξ|φτιαξ|plan|κάνε|κανε)", m):
        return {"intent": "missions_list", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}

    if re.search(r"\b(στόχοι|στοχοι|goals)\b", m) and not re.search(r"(δημιούργ|δημιουργ|βάλε|βαλε|πρόσθεσε|create)", m):
        return {"intent": "goals_list", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}

    if re.search(r"\b(τι\s+μπορείς|τι\s+μπορεις|τι\s+κάνεις\s+εσύ|βοήθεια|help)\b", m):
        return {"intent": "capabilities", "confidence": 0.88, "slots": {}, "clarification_question": None, "source": "rules"}
    if re.search(r"\b(ποιος\s+είσαι|ποιος\s+εισαι|πώς\s+σε\s+λένε|πως\s+σε\s+λενε)\b", m):
        return {"intent": "identity", "confidence": 0.9, "slots": {}, "clarification_question": None, "source": "rules"}

    if re.search(
        r"\b(θυμάσαι|θυμασαι|θυμήσου|θυμησου|τι\s+θυμάσαι|τι\s+θυμασαι|"
        r"τι\s+είχαμε\s+πει|τι\s+ειχαμε\s+πει|recall|remember)\b",
        m,
    ):
        q = re.sub(
            r"^(?:θυμάσαι|θυμασαι|θυμήσου|θυμησου|recall|remember)\s+(?:ότι|οτι|για|το|τα|αν)?\s*",
            "",
            message.strip(),
            flags=re.IGNORECASE,
        ).strip(" ?!.·")
        return {
            "intent": "memory_recall",
            "confidence": 0.9,
            "slots": {"query": q or message.strip()},
            "clarification_question": None,
            "source": "rules",
        }

    mission_match = re.match(
        r"^(?:δημιούργησε|δημιουργησε|φτιάξε|φτιαξε|κάνε|κανε|plan)\s+(?:μου\s+)?(?:μία?\s+|μια\s+|ένα\s+)?(?:αποστολή|αποστολη|mission)\s*[:\-]?\s*(.+)$",
        message.strip(),
        re.IGNORECASE,
    )
    if mission_match:
        return {
            "intent": "create_mission",
            "confidence": 0.95,
            "slots": {"goal": mission_match.group(1).strip()},
            "clarification_question": None,
            "source": "rules",
        }

    goal_match = re.match(
        r"^(?:δημιούργησε|δημιουργησε|βάλε|βαλε|πρόσθεσε|προσθεσε|create)\s+(?:(?:έναν?|a)\s+)?(?:στόχο|στοχο|goal)\s*[:\-]?\s*(.+)$",
        message.strip(),
        re.IGNORECASE,
    )
    if goal_match:
        return {
            "intent": "create_goal",
            "confidence": 0.95,
            "slots": {"title": goal_match.group(1).strip()},
            "clarification_question": None,
            "source": "rules",
        }

    search_match = re.match(
        r"^(?:ψάξε|ψαξε|αναζήτησε|αναζητησε|search)\s+(?:για\s+|στο\s+διαδίκτυο\s+|online\s+)?(.+)$",
        message.strip(),
        re.IGNORECASE,
    )
    if search_match:
        return {
            "intent": "search_web",
            "confidence": 0.93,
            "slots": {"query": search_match.group(1).strip()},
            "clarification_question": None,
            "source": "rules",
        }

    urls = re.findall(r"https?://[^\s]+", message or "")
    if urls and re.search(r"\b(διάβασε|διαβασε|άνοιξε|ανοιξε|read|open)\b", m):
        return {
            "intent": "read_url",
            "confidence": 0.94,
            "slots": {"url": urls[0].rstrip(".,);")},
            "clarification_question": None,
            "source": "rules",
        }
    um = re.match(r"^(?:διάβασε|διαβασε|read)\s+(https?://\S+)", message.strip(), re.IGNORECASE)
    if um:
        return {
            "intent": "read_url",
            "confidence": 0.95,
            "slots": {"url": um.group(1).rstrip(".,);")},
            "clarification_question": None,
            "source": "rules",
        }

    if re.search(r"\b(εξέλιξη|εξελιξη|self[- ]?improve|self[- ]?improvement|βελτίωσε\s+τον\s+εαυτό|βελτιωσε\s+τον\s+εαυτο)\b", m):
        return {
            "intent": "evolve",
            "confidence": 0.9,
            "slots": {},
            "clarification_question": None,
            "source": "rules",
        }

    if re.search(r"\b(σταμάτα|σταματα|stop)\s+(την\s+)?(αυτόνομη|αυτονομη|autonomous)\b", m) or re.search(
        r"\b(απενεργοποίησε|απενεργοποιησε)\s+(την\s+)?(αυτόνομη|αυτονομη|autonomous)\b", m
    ):
        return {
            "intent": "autonomous_stop",
            "confidence": 0.93,
            "slots": {},
            "clarification_question": None,
            "source": "rules",
        }
    if re.search(r"\b(ξεκίνα|ξεκινα|ενεργοποίησε|ενεργοποιησε|start)\s+(την\s+)?(αυτόνομη|αυτονομη|autonomous)\b", m):
        return {
            "intent": "autonomous_start",
            "confidence": 0.93,
            "slots": {},
            "clarification_question": None,
            "source": "rules",
        }
    if re.search(r"\b(αυτόνομη|αυτονομη|autonomous)\s+(λειτουργία|λειτουργια|mode|status|κατάσταση|κατασταση)\b", m) or re.search(
        r"\b(κατάσταση|κατασταση)\s+(αυτόνομης|αυτονομης|autonomous)\b", m
    ):
        return {
            "intent": "autonomous_status",
            "confidence": 0.9,
            "slots": {},
            "clarification_question": None,
            "source": "rules",
        }

    return None


_CLASSIFIER_SYSTEM = """Είσαι ο ταξινομητής προθέσεων του ΝΟΥΣ AI OS.
Δέχεσαι ένα μήνυμα χρήστη στα ελληνικά (ή μεικτά) και επιστρέφεις ΜΟΝΟ έγκυρο JSON, χωρίς markdown, χωρίς εξηγήσεις έξω από το JSON.

Διαθέσιμα intents:
- system_status, health_check, missions_list, goals_list
- create_mission (slots: goal), create_goal (slots: title)
- search_web (slots: query), deep_research (slots: query), read_url (slots: url)
- memory_recall (slots: query), knowledge_query, evolve
- autonomous_start / autonomous_stop / autonomous_status
- capabilities, identity, calculator, general_chat, unclear

Κανόνες:
1. confidence 0.0–1.0.
2. Αν λείπει slot ή confidence < 0.55 → intent=unclear + clarification_question στα ελληνικά.
3. Μην εφευρίσκεις intents.
4. Αόριστες φράσεις → unclear.
5. create_mission/create_goal εκτελούνται απευθείας (όχι /plan).

Παράδειγμα:
{"intent":"system_status","confidence":0.88,"slots":{},"clarification_question":null,"reasoning":"κατάσταση"}
"""


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

    turns = [{"role": "user", "content": f"Μήνυμα χρήστη:\n{message}"}]
    try:
        result = ask_with_turns(turns, system=_CLASSIFIER_SYSTEM)
    except Exception:
        return None

    if not result or not result.get("success"):
        return None

    raw = result.get("response") or result.get("text") or ""
    data = _extract_json(raw)
    if not data:
        return None

    intent = str(data.get("intent") or "unclear").strip().lower()
    if intent not in KNOWN_INTENTS:
        intent = "unclear"

    try:
        confidence = float(data.get("confidence", 0.5))
    except Exception:
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    slots = data.get("slots") if isinstance(data.get("slots"), dict) else {}
    clarification = data.get("clarification_question")
    if clarification is not None:
        clarification = str(clarification).strip() or None

    return {
        "intent": intent,
        "confidence": confidence,
        "slots": slots,
        "clarification_question": clarification,
        "source": "llm",
        "reasoning": data.get("reasoning"),
    }


def classify_intent(message: str, use_llm: bool = True) -> dict[str, Any]:
    message = (message or "").strip()
    if not message:
        return {
            "intent": "unclear",
            "confidence": 0.0,
            "slots": {},
            "clarification_question": "Πες μου τι θα ήθελες να κάνουμε;",
            "source": "fallback",
            "needs_clarification": True,
        }

    ruled = _rule_based(message)
    if ruled and ruled["confidence"] >= CONFIDENCE_ACT:
        ruled["needs_clarification"] = False
        return ruled

    if use_llm:
        llm_result = _llm_classify(message)
        if llm_result:
            conf = llm_result["confidence"]
            intent = llm_result["intent"]
            slots = llm_result.get("slots") or {}

            needs = False
            question = llm_result.get("clarification_question")

            if intent == "unclear" or conf < CONFIDENCE_CLARIFY:
                needs = True
            elif intent == "create_mission" and not slots.get("goal"):
                needs = True
                question = question or "Τι στόχο θέλεις να έχει η αποστολή;"
            elif intent == "create_goal" and not slots.get("title"):
                needs = True
                question = question or "Πώς να ονομάσουμε τον στόχο;"
            elif intent == "search_web" and not slots.get("query"):
                needs = True
                question = question or "Τι να ψάξω ακριβώς;"
            elif intent == "read_url" and not slots.get("url"):
                needs = True
                question = question or "Ποιο URL να ανοίξω;"
            elif conf < CONFIDENCE_ACT and intent not in (
                "general_chat",
                "capabilities",
                "identity",
                "memory_recall",
                "evolve",
                "autonomous_status",
            ):
                needs = True
                if not question:
                    question = f"Κατάλαβα ότι θέλεις «{intent}». Να προχωρήσω;"

            if needs and not question:
                question = "Δεν είμαι σίγουρος τι ακριβώς θέλεις. Μπορείς να το πεις λίγο πιο συγκεκριμένα;"

            llm_result["needs_clarification"] = needs
            llm_result["clarification_question"] = question if needs else None
            return llm_result

    if ruled:
        ruled["needs_clarification"] = ruled["confidence"] < CONFIDENCE_ACT
        return ruled

    return {
        "intent": "general_chat",
        "confidence": 0.5,
        "slots": {},
        "clarification_question": None,
        "source": "fallback",
        "needs_clarification": False,
    }


def format_clarification_response(classification: dict[str, Any]) -> dict[str, Any]:
    question = classification.get("clarification_question") or "Μπορείς να μου εξηγήσεις λίγο περισσότερο τι θέλεις;"
    return {
        "ok": True,
        "source": "intent_classifier",
        "mode": "clarification",
        "intent": classification.get("intent", "unclear"),
        "confidence": classification.get("confidence", 0.0),
        "answer": question,
        "response": question,
        "text": question,
        "executed": False,
        "needs_clarification": True,
    }
