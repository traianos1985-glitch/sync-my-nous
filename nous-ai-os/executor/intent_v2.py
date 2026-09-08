def normalize(t):
    t = str(t).lower()
    t = t.replace("\n", " ").replace("\r", " ")
    return " ".join(t.split()).strip()


def match(intent_text, options):
    t = normalize(intent_text)
    for opt in options:
        if opt in t:
            return True
    return False


def detect(command):

    t = normalize(command)

    if match(t, ["τι κάνεις", "status", "κατάσταση"]):
        return "status"

    if match(t, ["evolve", "εξέλιξη", "auto"]):
        return "evolve"

    if match(t, ["plugin", "plugins"]):
        return "plugins"

    if match(t, ["remember", "μνήμη"]):
        return "memory"

    return "unknown"
