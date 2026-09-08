from executor.agent_core import act

def run(command, context=None):

    if command.startswith("/"):
        return act(command, context)

    from executor.brain import think

    raw = think(command, context)

    if isinstance(raw, dict):
        return raw.get("response", str(raw))

    return str(raw)
