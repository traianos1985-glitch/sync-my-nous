from executor.llm_core import ask
from executor.memory import load

def think(command, context=None):

    recent = load()[-8:]

    system_prompt = f"""
Είσαι ο ΝΟΥΣ AI OS, ένας ελαφρύς τοπικός agent που τρέχει σε Android/Termux.

Απάντα φυσικά στα ελληνικά.
Μην επιστρέφεις JSON.
Μην επιστρέφεις markdown fences.
Να είσαι πρακτικός, σύντομος και χρήσιμος.
Έχεις πρόσβαση σε μνήμη, plugins, internet tools και τοπικό Flask runtime.

Πρόσφατη μνήμη:
{recent}

Context:
{context}

Χρήστης:
{command}
"""
    return ask(system_prompt)
