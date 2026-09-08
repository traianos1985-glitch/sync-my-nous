import json
import os
import time

from executor.operator_capability_manager import operator_capabilities
from executor.code_assistant import run_cmd
from executor.agent_journal import write_journal

SCRIPTS_DIR = "data/browser_scripts"

def _ensure():
    os.makedirs(SCRIPTS_DIR, exist_ok=True)

def browser_driver_status():
    caps = operator_capabilities()
    return {
        "time": time.time(),
        "ready": bool(caps["browser_driver_ready"]),
        "node_ready": bool(caps["node_ready"]),
        "capabilities": caps,
        "supported_when_ready": ["open", "click", "fill", "screenshot"],
    }

def create_playwright_script(url, actions=None):
    _ensure()
    actions = actions or []
    sid = int(time.time_ns())
    path = f"{SCRIPTS_DIR}/{sid}.js"

    script = f'''
const {{ chromium }} = require('playwright');

(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.goto({json.dumps(url)}, {{ waitUntil: 'domcontentloaded', timeout: 30000 }});

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
    open(path, "w", encoding="utf-8").write(script)
    return path

def run_browser_actions(url, actions=None):
    status = browser_driver_status()
    if not status["ready"]:
        return {
            "ok": False,
            "error": "browser_driver_not_ready",
            "status": status,
        }

    script = create_playwright_script(url, actions or [])
    result = run_cmd(f"node {script}")
    output = {
        "ok": bool(result.get("ok")),
        "script": script,
        "result": result,
        "time": time.time(),
    }
    write_journal("browser_driver_actions", output)
    return output
