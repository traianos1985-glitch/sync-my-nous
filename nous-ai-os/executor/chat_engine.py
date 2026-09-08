def chat_fallback(text, context):

    return {
        "intent": "chat",
        "response": f"Μπορώ να σε βοηθήσω. Έγραψες: {text}",
        "mode": "simple_chat"
    }
