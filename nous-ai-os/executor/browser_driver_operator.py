"""Browser driver with a shared public-URL guard, honest host capability status and a
read-only fallback (url_reader_engine / web_search) when Playwright is absent (N-06)."""
import json
import os
import time

from executor.operator_capability_manager import operator_capabilities
from executor.code_assistant import run_cmd
from executor.agent_journal import write_journal
from executor.research_broker import validate_url

SCRIPTS_DIR = "data/browser_scripts"
# Actions that only observe a page can be satisfied by the HTTP reader fallback.
READ_ONLY_ACTIONS = {"open", "read", "extract", "screenshot_text", "wait"}
INTERACTIVE_ACTIONS = {"click", "fill"}
FALLBACK_ENGINES = ["url_reader_engine", "web_search"]


def _ensure():
    os.makedirs(SCRIPTS_DIR, exist_ok=True)


def guard_url(url):
    """Shared guard: http(s) only, public hosts only, no credentials/unusual ports.

    Returns (safe_url, None) or (None, reason). file://, localhost, private, link-local
    and metadata addresses are rejected before any script or request is created.
    """
    try:
        return validate_url(url), None
    except ValueError as exc:
        return None, str(exc) or "invalid_url"


def browser_driver_status():
    caps = operator_capabilities()
    ready = bool(caps.get("browser_driver_ready"))
    node_ready = bool(caps.get("node_ready"))
    if ready:
        host_support, reason = "available", None
    elif not node_ready:
        host_support, reason = "not_available_on_this_host", "node_not_installed"
    else:
        host_support, reason = "not_available_on_this_host", "playwright_not_installed"
    return {
        "time": time.time(),
        "ready": ready,
        "node_ready": node_ready,
        "host_support": host_support,
        "reason": reason,
        "fallback": {
            "available": not ready,
            "engines": FALLBACK_ENGINES,
            "supports": sorted(READ_ONLY_ACTIONS),
            "unsupported": sorted(INTERACTIVE_ACTIONS),
        },
        "capabilities": caps,
        "supported_when_ready": ["open", "click", "fill", "screenshot"],
    }


def _normalize_actions(actions):
    if actions is None:
        return []
    if not isinstance(actions, list) or len(actions) > 50:
        raise ValueError("invalid_actions")
    clean = []
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("type"), str):
            raise ValueError("invalid_actions")
        clean.append(action)
    return clean


def create_playwright_script(url, actions=None):
    _ensure()
    # Guard URL to fail closed on illegal schemes, private hosts/IPs or credentials
    safe_url = validate_url(url)
    actions = actions or []
    sid = int(time.time_ns())
    path = f"{SCRIPTS_DIR}/{sid}.js"

    script = f'''
const {{ chromium }} = require('playwright');

(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.goto({json.dumps(safe_url)}, {{ waitUntil: 'domcontentloaded', timeout: 30000 }});

  const actions = {json.dumps(actions)};
  for (const action of actions) {{
    if (action.type === "click") {{
      await page.click(action.selector);
    }}
    if (action.type === "fill") {{
      await page.fill(action.selector, action.value || "");
    }}
  }}

  console.log(JSON.stringify({{
    ok: true,
    url: page.url(),
    title: await page.title()
  }}));

  await browser.close();
}})().catch(err => {{
  console.error(String(err && err.stack || err));
  process.exit(1);
}});
'''
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(script)
    return path


def fallback_read(safe_url):
    """Read a guarded public page through the HTTP reader (no JS, no interaction)."""
    from executor.url_reader_engine import read_url

    page = read_url(safe_url)
    if not isinstance(page, dict) or not page.get("ok"):
        return {"ok": False, "error": (page or {}).get("error", "fallback_read_failed") if isinstance(page, dict) else "fallback_read_failed"}
    return {
        "ok": True,
        "url": safe_url,
        "title": page.get("title"),
        "text": str(page.get("text", ""))[:8000],
        "chars": page.get("chars"),
        "engine": "url_reader_engine",
    }


def fallback_search(query, max_results=5):
    from executor import web_search

    result = web_search.search(str(query or "").strip()[:500], max_results=max_results)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "search_failed")}
    return {"ok": True, "query": result.get("query"), "results": result.get("results", []),
            "count": result.get("count", 0), "engine": "web_search"}


def run_browser_actions(url, actions=None):
    safe_url, reason = guard_url(url)
    if safe_url is None:
        return {"ok": False, "error": f"invalid_url:{reason}"}
    try:
        actions = _normalize_actions(actions)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    status = browser_driver_status()
    if not status["ready"]:
        interactive = [a["type"] for a in actions if a["type"] not in READ_ONLY_ACTIONS]
        page = fallback_read(safe_url)
        output = {
            "mode": "fallback_url_reader",
            "host_support": status["host_support"],
            "reason": status["reason"],
            "url": safe_url,
            "page": page,
            "time": time.time(),
        }
        if interactive:
            # Honest: page content was read, but clicks/fills were NOT performed.
            output.update(ok=False, error="interactive_actions_not_available_on_this_host",
                          skipped_actions=interactive)
        else:
            output["ok"] = bool(page.get("ok"))
            if not page.get("ok"):
                output["error"] = page.get("error", "fallback_read_failed")
        write_journal("browser_driver_fallback", {k: v for k, v in output.items() if k != "page"})
        return output

    try:
        script = create_playwright_script(safe_url, actions)
    except ValueError as val_err:
        return {
            "ok": False,
            "error": f"invalid_url:{val_err}",
        }

    result = run_cmd(f"node {script}")
    output = {
        "ok": bool(result.get("ok")),
        "mode": "playwright",
        "script": script,
        "result": result,
        "time": time.time(),
    }
    write_journal("browser_driver_actions", output)
    return output
