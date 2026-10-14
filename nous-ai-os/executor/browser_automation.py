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
    from executor.guardian_policy import check_action
    from executor.action_journal import write_journal

    policy = check_action("research_query")
    if not policy.get("allowed"):
        return {"ok": False, "policy": policy}

    q = _clean_search_query(str(query or ""))
    if not q:
        return {"ok": False, "error": "empty_query", "answer": "Τι να ψάξω ακριβώς;"}

    try:
        from executor.internet_search_engine import answer_from_web

        web = answer_from_web(q)
        if isinstance(web, dict) and (web.get("answer") or web.get("results")):
            write_journal("browser_search", {"query": q, "via": "internet_search_engine"})
            return {
                "ok": True,
                "query": q,
                "answer": web.get("answer") or str(web.get("results", []))[:1200],
                "result": web,
                "source": "internet_search_engine",
            }
    except Exception:
        pass

    try:
        from executor.real_research_engine import research_query

        result = research_query(q, learn=False)
    except Exception as exc:
        write_journal("browser_search", {"query": q, "error": str(exc)})
        return {"ok": False, "error": str(exc), "answer": f"Αποτυχία αναζήτησης: {exc}"}

    write_journal("browser_search", {"query": q, "via": "research_query"})
    answer = None
    if isinstance(result, dict):
        answer = result.get("answer") or result.get("summary")
    return {
        "ok": True,
        "query": q,
        "answer": answer or str(result)[:1200],
        "result": result,
        "source": "research_query",
    }


def browser_read(url):
    from executor.guardian_policy import check_action
    from executor.action_journal import write_journal

    policy = check_action("browser_read")
    if not policy.get("allowed"):
        return {"ok": False, "policy": policy}
    try:
        from executor.real_research_engine import read_url

        result = read_url(url, learn=False)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    write_journal("browser_read", {"url": url})
    return {"ok": True, "result": result}
