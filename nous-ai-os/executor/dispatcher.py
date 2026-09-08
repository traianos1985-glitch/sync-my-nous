from executor.intent_v2 import detect
from executor.web_tools import search, fetch

def dispatch(command, context):

    if "http" in str(command):
        return fetch(command)

    if "search" in str(command):
        return search(command)


    intent = detect(command)

    if intent == "status":
        return "Νοῦς AI OS RUNNING"

    if intent == "evolve":
        return {"evolution": "started"}

    if intent == "plugins":
        return {"plugins": list(context.get("plugins", {}).keys())}

    if intent == "memory":
        return context.get("memory", {})

    return {
        "intent": intent,
        "output": "NO ACTION MATCHED"
    }
