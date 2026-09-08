from executor.intent import detect_intent
from executor.tools import run_tool
from executor.memory import save
from executor.hybrid_agent import run as hybrid_run


def handle(command, context=None):

    if context is None:
        context = {}

    context["command"] = command

    intent = detect_intent(command)

    save({
        "command": command,
        "intent": intent
    })

    t = intent["type"]

    if t == "system":

        if intent["action"] == "status":
            return {
                "output": "ΝΟΥΣ AI OS RUNNING",
                "type": "system"
            }

        if intent["action"] == "evolve":
            return {
                "output": "LEVEL 27 CORE ACTIVE",
                "type": "system"
            }

    if t == "tool":
        return {
            "output": run_tool(intent, context),
            "type": "tool"
        }

    try:
        result = hybrid_run(command, context)

        return {
            "output": result,
            "type": "reasoning"
        }

    except Exception as e:
        return {
            "output": f"REASONING ERROR: {e}",
            "type": "error"
        }
