import subprocess, time
from executor.operator_approval import request_approval, is_approved
from executor.agent_journal import write_journal

ANDROID_INPUT = "/system/bin/input"
ANDROID_AM = "/system/bin/am"

def _cmd(command):
    try:
        p = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=10)
        return {"ok": p.returncode == 0, "code": p.returncode, "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def android_operator_status():
    return {
        "mode": "approval_required_for_gestures",
        "supported": ["tap", "swipe", "input_text", "keyevent_back", "keyevent_home"],
        "blocked": ["send_sms", "payments", "delete_files", "unknown_destructive_actions"],
        "time": time.time(),
    }

def tap(x, y, approval_id=None):
    payload = {"x": int(x), "y": int(y)}
    if not approval_id:
        return request_approval("android_tap", payload, "tap requires approval")
    if not is_approved(approval_id):
        return {"ok": False, "error": "approval_required", "approval_id": approval_id}
    res = _cmd(f"{ANDROID_INPUT} tap {int(x)} {int(y)}")
    write_journal("android_tap", {"payload": payload, "result": res})
    return res

def swipe(x1, y1, x2, y2, duration=300, approval_id=None):
    payload = {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2), "duration": int(duration)}
    if not approval_id:
        return request_approval("android_swipe", payload, "swipe requires approval")
    if not is_approved(approval_id):
        return {"ok": False, "error": "approval_required", "approval_id": approval_id}
    res = _cmd(f"{ANDROID_INPUT} swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration)}")
    write_journal("android_swipe", {"payload": payload, "result": res})
    return res

def keyevent(name):
    codes = {"back": 4, "home": 3, "enter": 66}
    if name not in codes:
        return {"ok": False, "error": "key_not_allowed"}
    res = _cmd(f"{ANDROID_INPUT} keyevent {codes[name]}")
    write_journal("android_keyevent", {"name": name, "result": res})
    return res


def operator_capabilities():
    import os
    return {
        "input": ANDROID_INPUT,
        "input_exists": os.path.exists(ANDROID_INPUT),
        "am": ANDROID_AM,
        "am_exists": os.path.exists(ANDROID_AM),
        "real_gestures_binary": os.path.exists(ANDROID_INPUT),
        "real_gestures_permission": gesture_permission_test().get("allowed"),
    }


def gesture_permission_test():
    result = _cmd(f"{ANDROID_INPUT} keyevent 4")
    allowed = bool(result.get("ok"))
    return {
        "allowed": allowed,
        "result": result,
        "reason": None if allowed else "INJECT_EVENTS permission required or input injection blocked",
    }
