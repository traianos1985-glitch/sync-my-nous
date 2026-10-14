MODE = {
    "autonomous": False
}


def enable():
    MODE["autonomous"] = True
    return status()


def disable():
    MODE["autonomous"] = False
    return status()


def status():
    return dict(MODE)
