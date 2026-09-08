from executor.intent_engine import parse_intent
from executor.response_guard import ensure_output
from executor.chat_engine import chat_fallback

def process(command, context):

    intent = parse_intent(command)

    if intent["action"] == "show_status":
        result = "ΝΟΥΣ AI OS RUNNING"

    elif intent["action"] == "run_evolution":
        result = "EVOLUTION ENGINE ACTIVE"

    elif intent["action"] == "manage_plugins":
        result = "PLUGIN SYSTEM READY"

    else:
        # 🧠 THIS IS THE KEY FIX
        result = chat_fallback(command, context)

    clean = ensure_output(result)

    return {
        "input": command,
        "intent": intent,
        "output": clean,
        "status": "ok"
    }
