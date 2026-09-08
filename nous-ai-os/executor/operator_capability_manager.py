import os
import time
from executor.code_assistant import run_cmd

COMMANDS = {
    "node": "command -v node",
    "npm": "command -v npm",
    "npx": "command -v npx",
    "playwright": "command -v playwright",
    "chromium": "command -v chromium",
    "firefox": "command -v firefox",
    "vercel": "command -v vercel",
    "railway": "command -v railway",
    "render": "command -v render",
}

def command_available(name):
    r = run_cmd(COMMANDS[name])
    return bool(r.get("ok") and r.get("stdout", "").strip())

def operator_capabilities():
    caps = {name: command_available(name) for name in COMMANDS}
    return {
        "time": time.time(),
        "commands": caps,
        "browser_driver_ready": (caps.get("playwright") or caps.get("chromium") or caps.get("firefox")) and not os.path.exists("/data/data/com.termux"),
        "node_ready": caps.get("node") and caps.get("npm") and caps.get("npx"),
        "deploy_ready": caps.get("vercel") or caps.get("railway") or caps.get("render"),
        "install_hints": {
            "playwright": "npm install -g playwright && npx playwright install chromium",
            "vercel": "npm install -g vercel",
            "railway": "npm install -g @railway/cli",
        },
    }

def reality_flags():
    caps = operator_capabilities()
    return {
        "real_browser_clicks": bool(caps["browser_driver_ready"]),
        "real_browser_forms": bool(caps["browser_driver_ready"]),
        "real_hosting_deploy": bool(caps["deploy_ready"]),
        "can_install_browser_tools": bool(caps["node_ready"]),
    }
