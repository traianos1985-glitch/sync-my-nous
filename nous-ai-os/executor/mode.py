MODE = {
    "autonomous": False
}

def enable():
    MODE["autonomous"] = True

def status():
    return MODE
