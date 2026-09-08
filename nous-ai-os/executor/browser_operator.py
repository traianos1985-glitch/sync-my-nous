import time
from executor.operator_approval import request_approval, is_approved
from executor.agent_journal import write_journal
from executor.research_browser_agent import read_url

ALLOWED_DOMAINS = [
    "example.com",
    "flask.palletsprojects.com",
]

def _domain_allowed(url):
    return any(d in str(url) for d in ALLOWED_DOMAINS)

def browser_operator_status():
    return {
        "mode": "approval_required",
        "allowed_domains": ALLOWED_DOMAINS,
        "supported": ["open_url", "read_url", "prepare_click", "prepare_fill_form", "prepare_login"],
        "blocked": ["payments", "captcha_bypass", "unknown_domains_without_approval"],
        "time": time.time(),
    }

def open_url(url):
    if not _domain_allowed(url):
        return request_approval("browser_open_url", {"url": url}, "domain not allowlisted")
    result = read_url(url, learn=False)
    write_journal("browser_operator_open_url", {"url": url})
    return {"ok": True, "result": result}

def prepare_click(url, selector, approval_id=None):
    payload = {"url": url, "selector": selector}
    if not approval_id:
        return request_approval("browser_click", payload, "click requires approval")
    if not is_approved(approval_id):
        return {"ok": False, "error": "approval_required", "approval_id": approval_id}
    write_journal("browser_click_approved", payload)
    return {"ok": True, "prepared": True, "note": "Click approved. Real browser driver comes in Operator Pack 2.", "payload": payload}

def prepare_fill_form(url, fields, approval_id=None):
    payload = {"url": url, "fields": fields}
    if not approval_id:
        return request_approval("browser_fill_form", payload, "form fill requires approval")
    if not is_approved(approval_id):
        return {"ok": False, "error": "approval_required", "approval_id": approval_id}
    write_journal("browser_fill_form_approved", payload)
    return {"ok": True, "prepared": True, "note": "Form fill approved. Real browser driver comes in Operator Pack 2.", "payload": payload}

def prepare_login(url, username_field="username", password_field="password"):
    return request_approval(
        "browser_login",
        {"url": url, "username_field": username_field, "password_field": password_field},
        "login requires explicit approval and no password storage"
    )
