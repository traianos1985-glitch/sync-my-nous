import time

from executor.research_agent import web_search, fetch_page
from executor.curiosity_agent import mark_learned
from executor.memory import save


def research_query(query, learn=False, topic=None):
    q = str(query).strip()
    result = web_search(q)

    output = {
        "query": q,
        "result": result,
        "learned": None,
        "time": time.time(),
    }

    if learn:
        output["learned"] = mark_learned(
            topic or q,
            summary=str(result)[:2000],
            source="internet_research"
        )

    save({"event": "research_query", "query": q, "learn": learn})
    return output


def read_url(url, learn=False, topic=None):
    u = str(url).strip()
    result = fetch_page(u)

    output = {
        "url": u,
        "content": result,
        "learned": None,
        "time": time.time(),
    }

    if learn:
        output["learned"] = mark_learned(
            topic or u,
            summary=str(result)[:3000],
            source="web_page"
        )

    save({"event": "browser_read_url", "url": u, "learn": learn})
    return output
