import time
from executor.research_browser_agent import read_url, research_query
from executor.guardian_policy import check_action
from executor.agent_journal import write_journal

def browser_status():
    return {
        "mode": "safe_http_reader",
        "actions": ["search", "read_url"],
        "blocked": ["click_forms", "login", "payments", "destructive_actions"],
        "time": time.time(),
    }

def browser_search(query):
    policy = check_action("research_query")
    if not policy.get("allowed"):
        return {"ok": False, "policy": policy}
    result = research_query(query, learn=False)
    write_journal("browser_search", {"query": query})
    return {"ok": True, "result": result}

def browser_read(url):
    policy = check_action("browser_read")
    if not policy.get("allowed"):
        return {"ok": False, "policy": policy}
    result = read_url(url, learn=False)
    write_journal("browser_read", {"url": url})
    return {"ok": True, "result": result}
