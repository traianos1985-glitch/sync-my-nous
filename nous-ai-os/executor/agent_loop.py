"""
NOUS Agent Loop — ReAct pattern
Ο LLM αποφασίζει ο ίδιος πότε να χρησιμοποιήσει tools.
"""
from __future__ import annotations

import re
from typing import Any
from pathlib import Path

DATA = Path("data")

AGENT_SYSTEM = """Είσαι ο ΝΟΥΣ, έξυπνος AI βοηθός που μιλά ελληνικά.

Έχεις πρόσβαση στα εξής tools — χρησιμοποίησέ τα ΜΟΝΟ αν χρειάζεσαι:
  TOOL:search_web(ερώτημα)        → για νέα, τρέχοντα γεγονότα, τιμές, ειδήσεις
  TOOL:search_wikipedia(ερώτημα) → για ορισμούς, ιστορία, επιστήμη, βιογραφίες
  TOOL:search_memory(ερώτημα)    → για ό,τι έχει αποθηκευτεί στη μνήμη μου

Κανόνες:
1. Ερωτήσεις γνώμης, εκτίμησης, αυτοαξιολόγησης (π.χ. "πιστεύεις ότι...", "χρειάζεσαι...", "τι νομίζεις...") → απάντα ΑΠΕΥΘΕΙΑΣ χωρίς tool.
2. Ερωτήσεις για τον εαυτό σου, τις δυνατότητές σου, την κατάστασή σου → απάντα ΑΠΕΥΘΕΙΑΣ.
3. Τρέχοντα γεγονότα / νέα / τιμές που αλλάζουν → χρησιμοποίησε TOOL:search_web
4. Σταθερή γνώση που δεν αλλάζει (ιστορία, επιστήμη, ορισμοί) → χρησιμοποίησε TOOL:search_wikipedia
5. Αν δεν είσαι σίγουρος αν ξέρεις → απάντα από μόνος σου, αλλά πες ότι δεν είσαι 100% σίγουρος.
6. Μη δημιουργείς αποστολές, μην επιστρέφεις JSON, μην χρησιμοποιείς markdown υπερβολικά.
7. Απάντα πάντα στα ελληνικά.

Αν αποφασίσεις να χρησιμοποιήσεις tool, γράψε ΜΟΝΟ μία γραμμή:
TOOL:search_web(το ερώτημά σου)
ή
TOOL:search_wikipedia(το ερώτημά σου)

Μετά το αποτέλεσμα, δώσε την τελική απάντηση στα ελληνικά."""


def _parse_tool_call(text: str) -> tuple[str, str] | None:
    text = text.strip()
    m = re.search(r"TOOL:(search_web|search_wikipedia|search_memory)\((.+?)\)", text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).lower(), m.group(2).strip(" \"'")
    return None


def _run_tool(tool: str, query: str) -> str:
    try:
        if tool == "search_web":
            from executor.internet_search_engine import answer_from_web
            result = answer_from_web(query)
            items = result.get("results", [])
            if not items:
                return result.get("answer", "Δεν βρήκα αποτελέσματα.")
            parts = []
            for r in items[:3]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")[:300]
                url = r.get("url", "")
                parts.append(f"• {title}: {snippet} ({url})")
            return "\n".join(parts)

        elif tool == "search_wikipedia":
            from executor.internet_search_engine import _wikipedia_search
            items = _wikipedia_search(query)
            if not items:
                return "Δεν βρήκα αποτέλεσμα στη Wikipedia."
            r = items[0]
            title = r.get("title", "")
            snippet = r.get("snippet", "")[:600]
            url = r.get("url", "")
            return f"Wikipedia — {title}:\n{snippet}\n{url}"

        elif tool == "search_memory":
            from executor.knowledge_memory_engine import search_knowledge
            hits = search_knowledge(query, limit=3)
            if not hits:
                return "Δεν βρήκα σχετική μνήμη."
            parts = [h.get("content", "")[:200] for h in hits[:3] if h.get("content")]
            return "\n".join(parts) or "Δεν βρήκα σχετική μνήμη."

    except Exception as e:
        return f"(Το tool απέτυχε: {e})"
    return "Άγνωστο tool."


def run_agent(message: str, conversation_id: str | None = None, extra_context: str = "") -> dict[str, Any]:
    """
    ReAct agent:
    1. LLM αποφασίζει αν χρειάζεται tool ή απαντά απευθείας
    2. Αν tool → εκτέλεσε → δώσε αποτέλεσμα στο LLM → τελική απάντηση
    """
    try:
        from executor.remote_llm import ask_with_turns
        from executor.chat_brain_v3 import (
            build_llm_turns, looks_corrupted_answer, safe_llm_fallback,
            document_context_for_llm,
        )
        from executor.knowledge_memory_engine import coding_context
        from executor.error_learning_engine import engineering_memory_context
    except Exception as e:
        return {"ok": False, "answer": f"Agent init error: {e}", "mode": "agent_error"}

    doc_ctx = document_context_for_llm(message)
    code_ctx = coding_context(message)
    eng_ctx = engineering_memory_context(message)

    system = AGENT_SYSTEM
    if extra_context:
        system += f"\n\nΠρόσθετο πλαίσιο:\n{extra_context}"
    if doc_ctx:
        system += f"\n\n{doc_ctx}"
    if code_ctx:
        system += f"\n\nΚώδικας στη μνήμη:\n{code_ctx}"
    if eng_ctx:
        system += f"\n\nΜνήμη μηχανικής:\n{eng_ctx}"

    turns = build_llm_turns(message, conversation_id)
    tool_used = None
    tool_result = None

    # Γύρος 1 — LLM αποφασίζει
    try:
        r1 = ask_with_turns(turns, system=system)
        response1 = (r1.get("response", "") if isinstance(r1, dict) else "").strip()
    except Exception as e:
        return {"ok": False, "answer": "Σφάλμα επικοινωνίας με το LLM.", "mode": "agent_error"}

    if not response1:
        return {"ok": False, "answer": "Δεν πήρα απάντηση.", "mode": "agent_error"}

    tool_call = _parse_tool_call(response1)

    if tool_call:
        tool_name, query = tool_call
        tool_used = tool_name
        tool_result = _run_tool(tool_name, query)

        # Γύρος 2 — LLM παίρνει αποτέλεσμα και απαντά
        turns2 = list(turns)
        turns2.append({"role": "assistant", "content": f"TOOL:{tool_name}({query})"})
        turns2.append({
            "role": "user",
            "content": (
                f"Αποτέλεσμα tool:\n\n{tool_result}\n\n"
                f"Τώρα απάντησε στην αρχική ερώτηση βασισμένος σε αυτό. "
                f"Μην ξαναζητήσεις tool."
            )
        })
        try:
            r2 = ask_with_turns(turns2, system=system)
            response2 = (r2.get("response", "") if isinstance(r2, dict) else "").strip()
            final = response2 if response2 else response1
        except Exception:
            final = response1
    else:
        final = response1

    if looks_corrupted_answer(final):
        final = safe_llm_fallback()

    return {
        "ok": True,
        "answer": final,
        "response": final,
        "text": final,
        "human_answer": final,
        "mode": "agent_loop",
        "tool_used": tool_used,
        "tool_query": tool_call[1] if tool_call else None,
        "tool_result": tool_result,
        "sources": [],
        "executed": False,
        "source": "agent_loop",
    }
