from executor.personal_agent import load_db
from executor.memory import load


GENERIC_RECALL_QUERIES = {
    "",
    "recall",
    "θυμάσαι",
    "τι θυμάσαι",
    "τι θυμασαι",
    "τι ξέρεις για μένα",
    "τι ξερεις για μενα",
    "who am i",
    "profile",
    "μνήμη",
    "μνημη",
}


def clean_query(query=""):
    q = str(query).lower().strip()
    q = q.strip("?.!,;:·…")
    return q


def as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    if value:
        return [value]
    return []


def format_memory_item(item):
    if isinstance(item, dict):
        if "goal" in item:
            return item.get("goal", "")
        if "project" in item:
            project = item.get("project", "")
            steps = item.get("steps", [])
            if steps and isinstance(steps, list):
                first = steps[0]
                if isinstance(first, dict) and first.get("step"):
                    return f"{project} — επόμενο βήμα: {first.get('step')}"
            return project
        if "command" in item:
            return item.get("command", "")
        if "event" in item:
            return f"event: {item.get('event')}"
    return str(item)

def recall(query=""):
    db = load_db()
    mem = load()

    q = clean_query(query)
    generic = q in GENERIC_RECALL_QUERIES

    profile = []
    goals = []
    projects = []
    memories = []

    for k, v in db.get("profile", {}).items():
        text = str(v)
        if generic or q in text.lower():
            profile.append(text)

    for g in as_list(db.get("goals", [])):
        text = format_memory_item(g)
        if generic or q in text.lower():
            goals.append(text)

    for p in as_list(db.get("projects", [])):
        text = format_memory_item(p)
        if generic or q in text.lower():
            projects.append(text)

    for item in mem[-100:]:
        text = format_memory_item(item)
        if generic or q in text.lower():
            memories.append(text)

    if not profile and not goals and not projects and not memories:
        return "Δεν βρήκα κάτι σχετικό στη μνήμη μου για αυτό."

    lines = []
    lines.append("Θυμάμαι τα εξής:")

    if profile:
        lines.append("")
        lines.append("Προφίλ:")
        for x in profile[:8]:
            lines.append(f"- {x}")

    if goals:
        lines.append("")
        lines.append("Στόχοι:")
        for x in goals[:8]:
            lines.append(f"- {x}")

    if projects:
        lines.append("")
        lines.append("Projects:")
        for x in projects[:8]:
            lines.append(f"- {x}")

    if memories:
        lines.append("")
        lines.append("Πρόσφατη μνήμη:")
        for x in memories[-8:]:
            lines.append(f"- {x}")

    return "\n".join(lines)
