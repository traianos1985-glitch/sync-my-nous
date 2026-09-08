def interpret_web(command):
    command = command.lower()

    if "ψάξε" in command or "search" in command:
        return "search"

    if "άνοιξε" in command or "fetch" in command:
        return "fetch"

    return None
