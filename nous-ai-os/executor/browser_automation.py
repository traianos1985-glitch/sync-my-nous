"""Browser automation helpers used by router chat intents."""

from __future__ import annotations

import re


def browser_status():
    return {"ok": True, "module": "browser_automation"}


def _clean_search_query(query: str) -> str:
    q = (query or "").strip()
    q = re.sub(
        r"^(?:ψάξε|ψαξε|αναζήτησε|αναζητησε|search|find)\s+",
        "",
        q,
        flags=re.IGNORECASE,
    )
    q = re.sub(r"^(?:για|for|στο\s+διαδίκτυο|online)\s+", "", q, flags=re.IGNORECASE)
    return q.strip(" :,-")


def browser_search(query):
    """Never raise — always return a dict for the router."""
    try:
        from executor.guardian_policy import check_action

        policy = check_action("research_query")
        if not policy.get("allowed"):
            return {
                "ok": False,
                "policy": policy,
                "error": "policy_blocked",
                "answer": "Η αναζήτηση μπλοκαρίστηκε από την πολιτική ασφαλείας.",
            }
    except Exception:
        pass

    q = _clean_search_query(str(query or ""))
    if not q:
        return {"ok": False, "error": "empty_query", "answer": "Τι να ψάξω ακριβώς;"}

    answer = None
    raw = None
    source = None

    try:
        from executor.internet_search_engine import answer_from_web

        web = answer_from_web(q)
        if isinstance(web, dict):
            raw = web
            answer = web.get("answer")
            if not answer and web.get("results"):
                answer = str(web.get("results"))[:1200]
            source = "internet_search_engine"
    except Exception as exc:
        raw = {"error": str(exc)}

    if not answer:
        try:
            from executor.real_research_engine import research_query

            result = research_query(q, learn=False)
            raw = result
            if isinstance(result, dict):
                answer = result.get("answer") or result.get("summary")
            if not answer:
                answer = str(result)[:1200]
            source = "research_query"
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "answer": f"Αποτυχία αναζήτησης: {exc}",
            }

    try:
        from executor.action_journal import write_journal

        write_journal("browser_search", {"query": q, "via": source})
    except Exception:
        pass

    return {
        "ok": True,
        "query": q,
        "answer": answer,
        "result": answer,
        "raw": raw,
        "source": source or "unknown",
    }


def browser_read(url):
    try:
        from executor.guardian_policy import check_action

        policy = check_action("browser_read")
        if not policy.get("allowed"):
            return {"ok": False, "policy": policy}
    except Exception:
        pass
    try:
        from executor.real_research_engine import read_url

        result = read_url(url, learn=False)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    try:
        from executor.action_journal import write_journal

        write_journal("browser_read", {"url": url})
    except Exception:
        pass
    return {"ok": True, "result": result}
