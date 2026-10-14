from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

CACHE = Path("data/internet_search_cache.json")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _tokenise_query(query: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "from", "how", "what", "when", "where", "why",
        "για", "στο", "στη", "της", "του", "και", "είναι", "ποιο", "ποια", "πως",
    }
    return {t for t in re.findall(r"[a-zA-Zα-ωΑ-Ω0-9]{3,}", (query or "").lower()) if t not in stop}


def _score_item(tokens: set[str], item: dict) -> float:
    """Token overlap + light domain boost for known product docs."""
    if not tokens:
        return 0.0
    blob = f"{item.get('title', '')} {item.get('snippet', '')} {item.get('url', '')}".lower()
    hits = sum(1 for t in tokens if t in blob)
    score = float(hits)
    url = (item.get("url") or "").lower()
    # Prefer official / documentation hosts for product-style queries.
    for domain, boost in (
        ("render.com", 1.5),
        ("docs.render.com", 2.0),
        ("github.com", 0.5),
        ("stackoverflow.com", 0.4),
        ("official", 0.3),
    ):
        if domain in url:
            score += boost
    return score


def _filter_relevant(
    query: str,
    results: list[dict],
    min_keep: int = 2,
    low_relevance_threshold: float = 1.5,
) -> tuple[list[dict], float, bool]:
    """Rank results, drop clear off-topic hits, report top score and low-relevance flag.

    Returns (ranked_results, top_score, is_low_relevance).
    is_low_relevance is True when the best hit is weak for multi-token product queries
    (e.g. "Render free tier" returning unrelated Shiny / GeForce hits).
    """
    if not results:
        return [], 0.0, True
    tokens = _tokenise_query(query)
    if not tokens:
        return results, 0.0, False

    scored = [(_score_item(tokens, r), r) for r in results]
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score = scored[0][0] if scored else 0.0

    good = [r for s, r in scored if s >= 1.0]
    ranked = [r for _, r in scored]
    if len(good) >= min_keep:
        ranked = good

    # Attach numeric score for downstream consumers / debugging.
    for s, r in scored:
        r["relevance_score"] = round(s, 2)

    is_low = top_score < low_relevance_threshold and len(tokens) >= 2
    return ranked, top_score, is_low


def _ddg_instant(query: str) -> list[dict]:
    try:
        import requests
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1, "skip_disambig": 1}
        r = requests.get(url, params=params, timeout=(4, 12), headers={"User-Agent": "NOUS-AI-OS/1.0"})
        data = r.json()
        results = []
        abstract = clean(data.get("AbstractText", ""))
        if abstract:
            results.append({
                "title": clean(data.get("Heading", query)),
                "url": data.get("AbstractURL", ""),
                "snippet": abstract,
                "source": "ddg_instant",
            })
        for rel in data.get("RelatedTopics", [])[:5]:
            if isinstance(rel, dict) and rel.get("Text"):
                results.append({
                    "title": clean(rel.get("Text", "")[:80]),
                    "url": rel.get("FirstURL", ""),
                    "snippet": clean(rel.get("Text", "")),
                    "source": "ddg_related",
                })
        return results
    except Exception:
        return []


def _wikipedia_search(query: str) -> list[dict]:
    try:
        import requests
        results = []
        for lang in ["el", "en"]:
            if results:
                break
            url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 4,
                "srprop": "snippet",
            }
            r = requests.get(url, params=params, timeout=12,
                             headers={"User-Agent": "NOUS-AI-OS/1.0 (nous@replit.app)"})
            data = r.json()
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                wiki_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
                results.append({
                    "title": clean(title),
                    "url": wiki_url,
                    "snippet": clean(snippet),
                    "source": f"wikipedia_{lang}",
                })
        return results
    except Exception:
        return []


def _ddg_html(query: str, limit: int = 5) -> list[dict]:
    try:
        import requests
        from bs4 import BeautifulSoup
        agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        for agent in agents:
            url = "https://duckduckgo.com/html/?q=" + quote_plus(query)
            r = requests.get(url, timeout=(4, 15), headers={
                "User-Agent": agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "el,en-US;q=0.9",
            })
            if r.status_code != 200:
                time.sleep(1)
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            for item in soup.select(".result, .web-result, article"):
                a = item.select_one("a.result__a, a[href], h2 a")
                sn = item.select_one(".result__snippet, .snippet, p")
                if not a:
                    continue
                href = a.get("href", "")
                if not href or href.startswith("/"):
                    continue
                results.append({
                    "title": clean(a.get_text(" ", strip=True)),
                    "url": href,
                    "snippet": clean(sn.get_text(" ", strip=True)) if sn else "",
                    "source": "ddg_html",
                })
                if len(results) >= limit:
                    break
            if results:
                return results
    except Exception:
        pass
    return []


def _llm_web_answer(query: str) -> str | None:
    try:
        from executor.remote_llm import ask_remote_llm
        prompt = (
            f"Ερώτηση χρήστη: {query}\n\n"
            "Απάντησε με βάση τις γνώσεις σου. Αν δεν ξέρεις σίγουρα πες το. "
            "Μην επινοείς συνδέσμους. Απάντα στα ελληνικά, σύντομα και ουσιαστικά."
        )
        r = ask_remote_llm(prompt)
        if r.get("success") and r.get("response"):
            return r["response"]
    except Exception:
        pass
    return None


def search_web(query: str, limit: int = 5) -> dict[str, Any]:
    q = clean(query)
    if not q:
        return {"ok": False, "error": "empty_query"}

    results = _ddg_instant(q)
    wiki = _wikipedia_search(q)
    if wiki:
        results = (results or []) + [w for w in wiki if w not in (results or [])]
    if len(results or []) < 2:
        html = _ddg_html(q, limit)
        if html:
            results = (results or []) + html

    results, top_score, low_relevance = _filter_relevant(q, results or [])

    if not results:
        results, top_score, low_relevance = _filter_relevant(
            q, _ddg_html(q, limit) or [], min_keep=1
        )

    payload: dict[str, Any] = {
        "ok": bool(results),
        "tool": "Internet Search Engine",
        "timestamp": now_iso(),
        "query": q,
        "results": results[:limit],
        "top_relevance_score": round(top_score, 2),
        "low_relevance": low_relevance,
    }
    if not results:
        payload["error"] = "no_results"
    elif low_relevance:
        payload["warning"] = "low_relevance_hits"

    try:
        cache = load_json(CACHE, [])
        if not isinstance(cache, list):
            cache = []
        cache.append(payload)
        save_json(CACHE, cache[-100:])
    except Exception:
        pass

    return payload


def answer_from_web(query: str) -> dict[str, Any]:
    res = search_web(query)
    results = res.get("results", [])
    low_relevance = bool(res.get("low_relevance"))
    llm_ans = None
    mode = "internet_search"

    if results and not low_relevance:
        lines = ["🔍 Βρήκα αυτά τα σχετικά αποτελέσματα:"]
        for i, x in enumerate(results[:4], 1):
            lines.append(f"\n**{i}. {x.get('title', 'Αποτέλεσμα')}**")
            sn = x.get("snippet", "")
            if sn:
                if len(sn) > 260:
                    sn = sn[:260].rstrip() + "..."
                lines.append(f"   {sn}")
            if x.get("url"):
                lines.append(f"   🔗 {x.get('url')}")
        answer = "\n".join(lines)
    else:
        # No hits OR weak relevance (e.g. product pricing queries that surface
        # unrelated DDG/Wikipedia pages) → LLM knowledge fallback.
        llm_ans = _llm_web_answer(query)
        if llm_ans:
            if results and low_relevance:
                mode = "llm_fallback_low_relevance"
                # Keep the weak hits as secondary context so the user can still open them.
                secondary = "\n".join(
                    f"- {x.get('title', '')}: {x.get('url', '')}" for x in results[:3]
                )
                answer = (
                    f"Τα live αποτελέσματα είχαν χαμηλή σχετικότητα για «{query}». "
                    f"Απάντηση με βάση γνώσεις + διαθέσιμες πηγές:\n\n{llm_ans}"
                )
                if secondary:
                    answer += f"\n\n_Δευτερεύουσες πηγές (χαμηλή relevance):_\n{secondary}"
            else:
                mode = "knowledge_fallback_no_web"
                answer = f"Δεν βρήκα live αποτελέσματα, αλλά με βάση τις γνώσεις μου:\n\n{llm_ans}"
        else:
            mode = "internet_search_empty"
            if results and low_relevance:
                lines = [
                    f"⚠️ Βρήκα αποτελέσματα, αλλά η σχετικότητά τους για «{query}» είναι χαμηλή:"
                ]
                for i, x in enumerate(results[:4], 1):
                    lines.append(f"\n**{i}. {x.get('title', 'Αποτέλεσμα')}**")
                    if x.get("url"):
                        lines.append(f"   🔗 {x.get('url')}")
                answer = "\n".join(lines)
            else:
                answer = "Δεν μπόρεσα να βρω αποτελέσματα γι' αυτή την αναζήτηση."

    return {
        "ok": bool(results) or bool(llm_ans),
        "web_ok": bool(res.get("ok")),
        "mode": mode,
        "low_relevance": low_relevance,
        "top_relevance_score": res.get("top_relevance_score", 0),
        "answer": answer,
        "results": results[:4],
        "raw": {
            "ok": bool(res.get("ok")),
            "query": res.get("query"),
            "results_count": len(results),
            "low_relevance": low_relevance,
            **({"error": res.get("error")} if res.get("error") else {}),
            **({"warning": res.get("warning")} if res.get("warning") else {}),
        },
    }
