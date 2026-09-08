from executor.android_sense import sense
from executor.notifications import notify

def battery_guard():
    data = sense()
    battery = data.get("battery", {})
    if not isinstance(battery, dict):
        return {"alert": False, "level": None, "plugged": None}
    level = battery.get("percentage") or battery.get("level")
    plugged = battery.get("plugged")

    if isinstance(level, int) and level <= 25 and plugged == "UNPLUGGED":
        notify("ΝΟΥΣ Battery Guard", f"Μπαταρία χαμηλή: {level}%. Καλό είναι να φορτίσεις.")
        return {"alert": True, "level": level}

    return {"alert": False, "level": level, "plugged": plugged}
