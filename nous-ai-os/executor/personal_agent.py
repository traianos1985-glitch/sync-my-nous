import time

from executor.llm_core import ask
from executor.json_object_store import edit_object, read_object, write_object

DB = "data/personal_agent.json"


def load_db():
    return read_object(DB)


def save_db(db):
    return write_object(DB, db)


def remember_fact(text):
    with edit_object(DB) as db:
        key = str(int(time.time_ns()))
        db["profile"][key] = text
    return {"saved": True, "fact": text}


def add_goal(text):
    with edit_object(DB) as db:
        item = {"id": int(time.time_ns()), "goal": text, "status": "active"}
        used = {str(existing.get("id")) for existing in db["goals"]}
        while str(item["id"]) in used:
            item["id"] += 1
        db["goals"].append(item)
    return item


def add_project(text):
    with edit_object(DB) as db:
        item = {"id": int(time.time_ns()), "project": text, "status": "active", "steps": []}
        used = {str(existing.get("id")) for existing in db["projects"]}
        while str(item["id"]) in used:
            item["id"] += 1
        db["projects"].append(item)
    return item


def list_state():
    return load_db()


def plan_goal(text):
    db = load_db()
    prompt = f"""
Είσαι ο ΝΟΥΣ AI OS ως προσωπικός συνεργάτης.
Φτιάξε πρακτικό σχέδιο στα ελληνικά.
Σημαντικό: Ο ΝΟΥΣ υπάρχει ήδη και τρέχει σε Android/Termux με Flask UI, remote LLM, plugins, memory, GitHub backup και tools.
Μην προτείνεις να χτιστεί από το μηδέν με Android Studio, iOS, Play Store ή νέο app.
Πρότεινε βήματα βελτίωσης του υπάρχοντος συστήματος.

Στόχος:
{text}

Προσωπικό context:
{db}

Δώσε:
1. σκοπό
2. βασικά βήματα
3. εργαλεία που χρειάζονται
4. ρίσκα
5. πρώτο άμεσο βήμα
"""
    res = ask(prompt)
    return res.get("response", str(res)) if isinstance(res, dict) else str(res)
