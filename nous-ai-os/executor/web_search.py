"""Web Search — αυτόνομη αναζήτηση πληροφοριών για τον NOUS.

Χρησιμοποιεί το υπάρχον internet_search_engine (DuckDuckGo / κ.α.).
"""
from __future__ import annotations
import time


def search(query: str, max_results: int = 5) -> dict:
    """Αναζητά στο web και επιστρέφει αποτελέσματα."""
    try:
        from executor.internet_search_engine import search_web
        results = search_web(query, limit=max_results)
        items = results if isinstance(results, list) else results.get("results", [])
        return {
            "ok":      True,
            "query":   query,
            "results": items[:max_results],
            "count":   len(items[:max_results]),
            "ts":      time.time(),
        }
    except Exception as e:
        return {"ok": False, "query": query, "error": str(e), "results": []}


def search_messenia(topic: str, max_results: int = 5) -> dict:
    """Εξειδικευμένη αναζήτηση για θέματα Μεσσηνίας / χρυσοθηρίας."""
    enhanced = f"{topic} Μεσσηνία site:el OR χρυσοθηρία αρχαιολογία"
    return search(enhanced, max_results=max_results)


def quick_fact(question: str) -> str:
    """Γρήγορη απάντηση μέσω LLM + web αναζήτηση."""
    try:
        results = search(question, max_results=3)
        context = "\n".join(
            f"- {r.get('title','')}: {r.get('snippet','')}"
            for r in results.get("results", [])
        )
        from executor.remote_llm import ask
        answer = ask(
            f"Απάντησε σύντομα (1-2 προτάσεις) στην ερώτηση: {question}\n"
            f"Πληροφορίες από web:\n{context}",
            system="Είσαι ο NOUS — βοηθός χρυσοθηρίας Μεσσηνίας. Απάντα στα Ελληνικά."
        )
        return answer
    except Exception as e:
        return f"Σφάλμα αναζήτησης: {e}"


def web_search_status() -> dict:
    try:
        r = search("test", max_results=1)
        return {"available": True, "engine": "internet_search_engine"}
    except Exception as e:
        return {"available": False, "error": str(e)}
