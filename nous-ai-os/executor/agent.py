from executor.intent_v2 import detect

def step(command, context):

    intent = detect(command)

    if intent == "status":
        return "OK"

    if intent == "evolve":
        return {
            "thinking": True,
            "next_action": "analyze_plugins"
        }

    if intent == "plugins":
        return list(context.get("plugins", {}).keys())

    return {"idle": True}
