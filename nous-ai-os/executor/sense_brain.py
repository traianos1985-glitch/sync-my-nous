from executor.android_sense import sense
from executor.memory import save

def sense_and_think():
    data = sense()

    battery = data.get("battery", {})
    level = battery.get("percentage") or battery.get("level")
    plugged = battery.get("plugged")
    temp = battery.get("temperature")

    notes = []

    if isinstance(level, int):
        if level <= 20:
            notes.append("Η μπαταρία είναι χαμηλή. Καλό είναι να το φορτίσεις σύντομα.")
        elif level <= 35:
            notes.append("Η μπαταρία είναι σχετικά χαμηλή. Πρόσεχε αν θέλεις να συνεχίσει να τρέχει ο ΝΟΥΣ.")
        else:
            notes.append("Η μπαταρία είναι σε αποδεκτό επίπεδο.")

    if plugged == "UNPLUGGED":
        notes.append("Το κινητό δεν είναι στην πρίζα.")
    else:
        notes.append("Το κινητό είναι συνδεδεμένο σε φόρτιση.")

    if isinstance(temp, (int, float)):
        if temp >= 40:
            notes.append("Η θερμοκρασία είναι αυξημένη. Καλό είναι να μην τρέχουν βαριά tasks.")
        else:
            notes.append(f"Η θερμοκρασία είναι φυσιολογική ({temp}°C).")

    clipboard = data.get("clipboard", "")
    if clipboard:
        notes.append("Υπάρχει κείμενο στο πρόχειρο που μπορώ να αναλύσω αν μου το ζητήσεις.")
    else:
        notes.append("Το πρόχειρο είναι άδειο.")

    out = "Παρατήρηση συσκευής:\n\n" + "\n".join(f"- {x}" for x in notes)

    save({
        "event": "sense_thought",
        "sense": data,
        "thought": out
    })

    return out
