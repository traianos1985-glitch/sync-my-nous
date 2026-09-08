from executor.llm_core import ask

def make_steps(goal):
    prompt = f"""
Είσαι planner agent για τον ΝΟΥΣ AI OS.

Σημαντικό context:
- Ο ΝΟΥΣ τρέχει σε Python/Flask μέσα σε Termux.
- Τα plugins είναι Python αρχεία μέσα στο executor/plugins/.
- Κάθε plugin πρέπει να έχει def run(): και να επιστρέφει dict.
- Μην προτείνεις JavaScript, plugin.json, manifest ή npm.
- Πρότεινε βήματα για το υπάρχον σύστημα.

Στόχος:
{goal}

Δώσε ΜΟΝΟ 5 πρακτικά βήματα, σύντομα, στα ελληνικά.
Μην γράψεις JSON.
"""
    res = ask(prompt)
    text = res.get("response", str(res)) if isinstance(res, dict) else str(res)

    steps = []
    for line in text.splitlines():
        line = line.strip("-• 1234567890. ")
        if line:
            steps.append(line)

    return steps[:5] or [
        "Ανάλυση στόχου",
        "Δημιουργία Python plugin με run()",
        "Έλεγχος ασφάλειας και compile",
        "Δοκιμή plugin",
        "Αποθήκευση στο executor/plugins/"
    ]
