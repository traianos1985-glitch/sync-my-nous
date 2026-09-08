from executor.personal_agent import load_db, save_db

def next_action(project_name=None):
    db = load_db()
    projects = db.get("projects", [])

    if not projects:
        return {"error": "no_projects"}

    project = projects[-1]
    if project_name:
        for p in projects:
            if project_name.lower() in p.get("project","").lower():
                project = p
                break

    step = {
        "step": "όρισε το επόμενο μικρό πρακτικό βήμα",
        "status": "suggested"
    }

    project.setdefault("steps", []).append(step)
    save_db(db)

    return {"project": project.get("project"), "next_action": step}
