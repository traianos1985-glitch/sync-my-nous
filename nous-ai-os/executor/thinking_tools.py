from executor.llm_core import ask
from executor.memory import load, save

def extract(res):
    if isinstance(res, dict):
        r = res.get("response")
        if r:
            return str(r).strip()
        if res.get("error"):
            return "LLM ERROR: " + str(res.get("error"))
        return str(res)
    if res:
        return str(res).strip()
    return "Δεν πήρα καθαρή απάντηση από το LLM."

def think_deep(prompt):
    recent = load()[-8:]
    q = f"""
Απάντα στα ελληνικά, καθαρά και ολοκληρωμένα.
Μην κόψεις την απάντηση στη μέση.
Να είσαι πρακτικός και όχι υπερβολικά μακροσκελής.

Θέμα:
{prompt}

Δώσε:
1. Περίληψη
2. Βασικά σημεία
3. Πρακτικές λύσεις
4. Ρίσκα
5. Επόμενο βήμα

Πρόσφατη μνήμη:
{recent}
"""
    out = extract(ask(q))
    save({"thinking_session": prompt, "result": out})
    return out

def solve_problem(prompt):
    q = f"""
Απάντα στα ελληνικά ως πρακτικός τεχνικός σύμβουλος.
Μην κόψεις την απάντηση στη μέση.

Πρόβλημα:
{prompt}

Δώσε:
- πιθανή αιτία
- διάγνωση
- βήματα λύσης
- τι να αποφύγω
- τελικό σχέδιο δράσης
"""
    return extract(ask(q))

def decide(prompt):
    q = f"""
Απάντα στα ελληνικά.
Βοήθησέ με να πάρω απόφαση.

Θέμα:
{prompt}

Δώσε:
- επιλογές
- υπέρ / κατά
- ρίσκα
- προτεινόμενη επιλογή
- γιατί
- επόμενο βήμα
"""
    return extract(ask(q))
