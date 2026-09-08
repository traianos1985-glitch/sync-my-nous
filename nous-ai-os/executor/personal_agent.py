import json, os, time
from executor.llm_core import ask

DB = "data/personal_agent.json"

def load_db():
    if not os.path.exists(DB):
        return {"profile": {}, "goals": [], "projects": [], "decisions": []}
    try:
        return json.load(open(DB, "r", encoding="utf-8"))
    except:
        return {"profile": {}, "goals": [], "projects": [], "decisions": []}

def save_db(db):
    os.makedirs("data", exist_ok=True)
    json.dump(db, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def remember_fact(text):
    db = load_db()
    db["profile"][str(int(time.time()))] = text
    save_db(db)
    return {"saved": True, "fact": text}

def add_goal(text):
    db = load_db()
    item = {"id": int(time.time()), "goal": text, "status": "active"}
    db["goals"].append(item)
    save_db(db)
    return item

def add_project(text):
    db = load_db()
    item = {"id": int(time.time()), "project": text, "status": "active", "steps": []}
    db["projects"].append(item)
    save_db(db)
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
