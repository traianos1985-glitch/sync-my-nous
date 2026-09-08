from executor.llm_core import ask
from executor.research_agent import web_search
from executor.code_forge import forge_plugin
from executor.memory import save

def _ask(role, goal):
    prompt = f"""
Είσαι ο ρόλος: {role}

Σημαντικό context ΝΟΥΣ AI OS:
- Τρέχει σε Android / Termux.
- Backend: Python 3.13 και Flask.
- Τα plugins είναι ΜΟΝΟ Python αρχεία μέσα στο executor/plugins/.
- Κάθε plugin πρέπει να έχει def run(): και να επιστρέφει dict.
- Μην προτείνεις npm, JavaScript, plugin.json, manifest ή Node εργαλεία.
- Μην ξανασχεδιάζεις τον ΝΟΥΣ από την αρχή.
- Πρότεινε μικρά, ασφαλή βήματα πάνω στο υπάρχον σύστημα.

Στόχος:
{goal}

Απάντα στα ελληνικά, πρακτικά, σύντομα.
"""
    res = ask(prompt)
    return res.get("response", str(res)) if isinstance(res, dict) else str(res)

def team_plan(goal):
    return {
        "planner": _ask("Planner - σπάει τον στόχο σε βήματα", goal),
        "researcher": _ask("Researcher - λέει τι πληροφορίες χρειάζονται", goal),
        "coder": _ask("Coder - λέει τι κώδικας χρειάζεται", goal),
        "reviewer": _ask("Reviewer - εντοπίζει ρίσκα και επόμενο βήμα", goal)
    }

def team_solve(goal):
    plan = team_plan(goal)
    actions = []

    if "plugin" in goal.lower() or "κώδικ" in goal.lower():
        actions.append({"forge_plugin": forge_plugin(goal)})

    if "ψάξε" in goal.lower() or "internet" in goal.lower() or "online" in goal.lower():
        actions.append({"research": web_search(goal)})

    result = {
        "goal": goal,
        "team": plan,
        "actions": actions,
        "status": "completed"
    }

    save({"event": "team_solve", "result": result})
    return result
