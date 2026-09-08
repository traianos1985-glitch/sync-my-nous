import subprocess
import json
import time
from executor.memory import save

def run_cmd(cmd):
    try:
        out = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=8
        )
        return out.strip()
    except Exception as e:
        return str(e)

def clipboard():
    return run_cmd(["termux-clipboard-get"])

def battery():
    out = run_cmd(["termux-battery-status"])
    try:
        return json.loads(out)
    except:
        return out

def device_info():
    out = run_cmd(["termux-telephony-deviceinfo"])
    try:
        return json.loads(out)
    except:
        return out

def sense():
    data = {
        "time": time.time(),
        "clipboard": clipboard(),
        "battery": battery(),
        "device": device_info()
    }

    save({
        "event": "android_sense",
        "data": data
    })

    return data
