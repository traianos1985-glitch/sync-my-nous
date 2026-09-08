from __future__ import annotations

import re
import json
import time
from pathlib import Path
from typing import Any

DATA = Path("data")

def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())

def is_natural_chat(message: str) -> bool:
    m = norm(message)
    patterns = [
        "τι κάνεις", "τι κανεις",
        "πως είσαι", "πώς είσαι", "πως εισαι",
        "καλημέρα", "καλημερα", "καλησπέρα", "καλησπερα",
        "γεια", "γειά",
        "με λένε", "με λενε",
        "εσένα", "εσενα",
        "πως σε λένε", "πώς σε λένε", "πως σε λενε",
        "ποιος είσαι", "ποιος εισαι",
        "τι μπορείς να κάνεις", "τι μπορεις να κανεις",
        "τι είναι να κάνεις", "τι ειναι να κανεις",
        "τι μπορείς", "τι μπορεις",
        "κατάσταση", "κατασταση", "status",
        "missions", "αποστολές", "αποστολες",
        "στόχοι", "στοχοι", "goals",
        "πόσα", "ποσα", "πόσες", "ποσες",
        "τι τρέχει", "τι τρεχει",
        "τι γίνεται", "τι γινεται",
        "πρόοδος", "προοδος", "progress",
    ]
    return any(x in m for x in patterns)


def _load(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _system_status_answer() -> str:
    missions_data = _load(DATA / "missions.json", [])
    goals_data = _load(DATA / "goals_v2.json", {})
    brain_data = _load(DATA / "brain_state.json", {})

    total_missions = len(missions_data) if isinstance(missions_data, list) else 0
    active = sum(1 for m in missions_data if isinstance(m, dict) and m.get("status") in ("active", "running")) if isinstance(missions_data, list) else 0
    done = sum(1 for m in missions_data if isinstance(m, dict) and m.get("status") == "done") if isinstance(missions_data, list) else 0
    blocked = sum(1 for m in missions_data if isinstance(m, dict) and m.get("status") == "blocked") if isinstance(missions_data, list) else 0

    goals_list = goals_data.get("goals", []) if isinstance(goals_data, dict) else []
    total_goals = len(goals_list)

    brain_level = brain_data.get("level", "—") if isinstance(brain_data, dict) else "—"

    lines = ["**Κατάσταση NOUS AI OS** ✅", ""]
    lines.append(f"• Σύστημα: **online**")
    lines.append(f"• Επίπεδο εγκεφάλου: **{brain_level}**")
    lines.append(f"• Αποστολές: **{total_missions}** συνολικά — {active} ενεργές, {done} ολοκληρωμένες, {blocked} blocked")
    lines.append(f"• Στόχοι: **{total_goals}** καταγεγραμμένοι")

    if total_goals > 0 and isinstance(goals_list, list):
        for g in goals_list[:3]:
            title = g.get("title") or g.get("goal") or str(g) if isinstance(g, dict) else str(g)
            lines.append(f"  — {title}")

    lines.append("")
    lines.append("Πες μου τι θέλεις να κάνουμε ή ρώτησέ με οτιδήποτε.")
    return "\n".join(lines)


def _missions_answer() -> str:
    missions_data = _load(DATA / "missions.json", [])
    if not isinstance(missions_data, list) or not missions_data:
        return "Δεν υπάρχουν αποστολές ακόμα. Μπορείς να δημιουργήσεις μία γράφοντας /plan <στόχος>."

    lines = [f"**Αποστολές** ({len(missions_data)} συνολικά):", ""]
    for m in missions_data[-8:]:
        if not isinstance(m, dict):
            continue
        title = m.get("title", "Αποστολή")
        status = m.get("status", "άγνωστη")
        emoji = {"active": "🔄", "running": "⚡", "done": "✅", "blocked": "❌", "pending": "⏳"}.get(status, "•")
        lines.append(f"{emoji} **{title}** — {status}")

    return "\n".join(lines)


def _goals_answer() -> str:
    goals_data = _load(DATA / "goals_v2.json", {})
    goals_list = goals_data.get("goals", []) if isinstance(goals_data, dict) else []
    if not goals_list:
        return "Δεν υπάρχουν καταγεγραμμένοι στόχοι ακόμα. Γράψε: στόχος <τι θέλεις να πετύχεις>"

    lines = [f"**Στόχοι** ({len(goals_list)} συνολικά):", ""]
    for g in goals_list[:8]:
        title = g.get("title") or g.get("goal") or str(g) if isinstance(g, dict) else str(g)
        lines.append(f"🎯 {title}")

    return "\n".join(lines)

def natural_chat_answer(message: str) -> dict[str, Any] | None:
    m = norm(message)

    # --- Ταυτότητα ---
    if any(x in m for x in ["με λένε", "με λενε", "εμένα με λένε", "εμενα με λενε"]):
        answer = "Χάρηκα! Εμένα μπορείς να με λες ΝΟΥΣ. Είμαι ο προσωπικός σου AI βοηθός μέσα στο NOUS AI OS."
        return pack(answer, "identity")

    if any(x in m for x in ["εσένα", "εσενα", "πως σε λένε", "πώς σε λένε", "πως σε λενε", "ποιος είσαι", "ποιος εισαι"]):
        answer = "Εμένα με λένε ΝΟΥΣ. Είμαι ο προσωπικός σου AI βοηθός για συζήτηση, κώδικα, έρευνα, έγγραφα, μνήμη και αποστολές. Ρώτα με ό,τι θέλεις στα ελληνικά!"
        return pack(answer, "identity")

    # --- Δυνατότητες ---
    if any(x in m for x in ["τι μπορείς", "τι μπορεις", "τι κάνεις εσύ", "τι κανεις εσυ", "βοήθεια", "βοηθεια", "help"]):
        answer = (
            "Μπορώ να σε βοηθήσω με:\n"
            "• **Φυσική συζήτηση** — ρώτα με ό,τι θέλεις στα ελληνικά\n"
            "• **Κώδικα** — ανάλυση, debug, βελτίωση\n"
            "• **Αναζήτηση internet** — πες «ψάξε για...»\n"
            "• **Έγγραφα** — ανέβασε PDF/Word και ρώτα γι' αυτό\n"
            "• **Μνήμη** — θυμάμαι τις συνομιλίες μας\n"
            "• **Αποστολές** — γράψε /plan <στόχος> για να δημιουργήσω αποστολή\n"
            "• **Κατάσταση** — πες «κατάσταση» για live εικόνα συστήματος"
        )
        return pack(answer, "capabilities")

    # --- Χαιρετισμοί ---
    if any(x in m for x in ["τι κάνεις", "τι κανεις", "πως είσαι", "πώς είσαι", "πως εισαι"]):
        answer = "Είμαι εδώ και λειτουργώ κανονικά! Πες μου τι θέλεις να δούμε."
        return pack(answer, "normal_chat")

    if any(x in m for x in ["καλημέρα", "καλημερα", "καλησπέρα", "καλησπερα", "γεια", "γειά", "hello", "hi"]):
        answer = "Γεια σου! Είμαι έτοιμος. Τι θέλεις να δούμε;"
        return pack(answer, "normal_chat")

    # --- Κατάσταση συστήματος ---
    if any(x in m for x in [
        "κατάσταση", "κατασταση", "status", "τι τρέχει", "τι τρεχει",
        "τι γίνεται", "τι γινεται", "πρόοδος", "προοδος", "progress",
        "πώς πάει", "πως παει", "τι έχουμε", "τι εχουμε"
    ]):
        return pack(_system_status_answer(), "system_status")

    # --- Αποστολές ---
    if any(x in m for x in [
        "missions", "αποστολές", "αποστολες", "αποστολη", "αποστολή",
        "πόσες αποστολές", "ποσες αποστολες", "τι αποστολές", "τι αποστολες",
        "ποιες αποστολές", "ποιες αποστολες"
    ]):
        return pack(_missions_answer(), "missions_list")

    # --- Στόχοι ---
    if any(x in m for x in [
        "στόχοι", "στοχοι", "goals", "στόχος", "στοχος",
        "τι στόχους", "τι στοχους", "ποιοι στόχοι", "ποιοι στοχοι"
    ]):
        return pack(_goals_answer(), "goals_list")

    # --- Δημιουργία αποστολής με φυσική γλώσσα ---
    mission_triggers = [
        "φτιάξε αποστολή", "φτιαξε αποστολη", "δημιούργησε αποστολή", "δημιουργησε αποστολη",
        "κάνε αποστολή", "κανε αποστολη", "νέα αποστολή", "νεα αποστολη",
        "ξεκίνα αποστολή", "ξεκινα αποστολη", "βάλε αποστολή", "βαλε αποστολη",
        "θέλω αποστολή", "θελω αποστολη", "create mission", "new mission"
    ]
    if any(x in m for x in mission_triggers):
        # Extract what comes after the trigger
        for trigger in mission_triggers:
            if trigger in m:
                idx = m.index(trigger) + len(trigger)
                goal = message[idx:].strip(" :—-")
                if goal:
                    answer = (
                        f"Εντάξει! Για να δημιουργήσω αποστολή για «{goal}», "
                        f"γράψε: /plan {goal}\n\n"
                        f"Ή αν θέλεις να εκτελεστεί αμέσως: /run {goal}"
                    )
                else:
                    answer = "Πες μου τον στόχο! Π.χ.: φτιάξε αποστολή βελτίωσε το UI"
                return pack(answer, "mission_guide")

    # --- Autonomous App Builder ---
    app_build_triggers = [
        "φτιάξε εφαρμογή", "φτιαξε εφαρμογη", "φτιάξε app", "φτιαξε app",
        "δημιούργησε εφαρμογή", "δημιουργησε εφαρμογη", "δημιούργησε app", "δημιουργησε app",
        "χτίσε εφαρμογή", "χτισε εφαρμογη", "χτίσε app", "χτισε app",
        "κάνε εφαρμογή", "κανε εφαρμογη",
        "build app", "build an app", "create app", "make app",
        "φτιάξε web app", "φτιαξε web app",
        "φτιάξε flask", "φτιαξε flask",
        "φτιάξε api", "φτιαξε api",
        "φτιάξε εργαλείο", "φτιαξε εργαλειο",
        "φτιάξε bot", "φτιαξε bot",
        "αυτόνομος builder", "autonomous app",
    ]
    if any(x in m for x in app_build_triggers):
        try:
            from executor.app_builder import plan_app
            result = plan_app(message)
            if result.get("ok"):
                plan = result["plan"]
                files_preview = "\n".join(
                    f"  • `{f.get('path')}` — {f.get('description', '')}"
                    for f in plan.get("files", [])[:8]
                )
                tech = ", ".join(plan.get("tech_stack", []))
                answer = (
                    f"## 🏗️ Σχέδιο Εφαρμογής: {plan.get('title')}\n\n"
                    f"**Τεχνολογία:** {tech}\n\n"
                    f"**Αρχεία που θα δημιουργηθούν:**\n{files_preview}\n\n"
                    f"**Εκτέλεση:** `{plan.get('run_command')}`\n\n"
                    f"---\n"
                    f"Έτοιμος να γράψω τα αρχεία. **Εγκρίνεις;**\n\n"
                    f"<app-approval plan_id=\"{plan['plan_id']}\" title=\"{plan.get('title')}\"></app-approval>"
                )
            else:
                answer = f"Δεν μπόρεσα να φτιάξω σχέδιο: {result.get('error', 'άγνωστο σφάλμα')}"
        except Exception as e:
            answer = f"Σφάλμα App Builder: {e}"
        return pack(answer, "app_builder_plan")

    # --- Code generation ---
    code_triggers = [
        "γράψε κώδικα", "γραψε κωδικα", "φτιάξε script", "φτιαξε script",
        "φτιάξε κώδικα", "φτιαξε κωδικα", "κώδικα για", "κωδικα για",
        "python script", "python κώδικα", "python κωδικα",
        "γράψε python", "γραψε python", "δημιούργησε κώδικα", "δημιουργησε κωδικα",
        "write code", "generate code", "create script",
        "φτιάξε πρόγραμμα", "φτιαξε προγραμμα", "γράψε πρόγραμμα", "γραψε προγραμμα",
    ]
    if any(x in m for x in code_triggers):
        try:
            from executor.remote_llm import ask_remote_llm
            prompt = (
                f"Ο χρήστης ζητάει:\n{message}\n\n"
                "Γράψε ολοκληρωμένο Python κώδικα που να λύνει ακριβώς αυτό το πρόβλημα. "
                "Πρόσθεσε σύντομη επεξήγηση στα ελληνικά πριν και μετά τον κώδικα. "
                "Χρησιμοποίησε markdown code blocks (```python ... ```)."
            )
            res = ask_remote_llm(prompt)
            if res.get("success") and res.get("response"):
                answer = res["response"]
            else:
                answer = "Δεν μπόρεσα να παράγω κώδικα αυτή τη στιγμή. Δοκίμασε πάλι."
        except Exception as e:
            answer = f"Σφάλμα κατά τη δημιουργία κώδικα: {e}"
        return pack(answer, "code_generation")

    # --- Scheduler από φυσική γλώσσα ---
    sched_triggers = [
        "προγραμμάτισε", "πρόγραμμάτισε", "programmatise", "schedule",
        "βάλε χρονοδιάγραμμα", "βαλε χρονοδιαγραμμα",
        "τρέξε κάθε", "τρεξε καθε", "εκτέλεσε κάθε", "εκτελεσε καθε",
        "κάνε αυτόματα", "κανε αυτοματα",
        "αυτόματη εκτέλεση", "αυτοματη εκτελεση",
    ]
    if any(x in m for x in sched_triggers):
        try:
            from executor.scheduler_agent import add_schedule, parse_schedule
            parsed = parse_schedule(message)
            if parsed and parsed.get("task"):
                item = add_schedule(message)
                stype = item.get("schedule_type", "interval")
                if stype == "interval":
                    secs = item.get("interval_seconds") or 3600
                    period = f"κάθε {secs // 60} λεπτά" if secs < 3600 else f"κάθε {secs // 3600} ώρα/ες"
                else:
                    period = f"καθημερινά {item.get('hour', 0):02d}:{item.get('minute', 0):02d}"
                answer = f"✅ Προγραμμάτισα: **{parsed['task']}** — {period}\n\nΑπό το μενού **Automation** μπορείς να δεις και να διαχειριστείς όλες τις αυτόματες εργασίες."
            else:
                answer = (
                    "Πες μου τι να προγραμματίσω και πότε. Παραδείγματα:\n\n"
                    "• «προγραμμάτισε έλεγχο κατάστασης κάθε 30 λεπτά»\n"
                    "• «προγραμμάτισε daily brief κάθε μέρα στις 9:00»\n"
                    "• «τρέξε αυτόματα κάθε 2 ώρες repair system»"
                )
        except Exception as e:
            answer = f"Σφάλμα scheduler: {e}. Δοκίμασε: «προγραμμάτισε X κάθε 30 λεπτά»"
        return pack(answer, "scheduler")

    # --- Αυτοβελτίωση ---
    if any(x in m for x in [
        "αυτοβελτί", "αυτοβελτι", "self-improv", "βελτιώνεσαι", "βελτιωνεσαι",
        "αναβαθμίζεσαι", "αναβαθμιζεσαι", "μαθαίνεις", "μαθαινεις",
        "μάθηση", "μαθηση", "εξέλιξη", "εξελιξη", "evolution"
    ]):
        answer = (
            "Ναι, έχω πραγματικό μηχανισμό αυτοβελτίωσης:\n\n"
            "• **Patch system** — μπορώ να προτείνω αλλαγές σε συγκεκριμένα αρχεία μου\n"
            "• **Απαιτεί έγκρισή σου** — για ασφάλεια, δεν τρέχω τίποτα χωρίς «ναι» από σένα\n"
            "• **Learning engine** — αποθηκεύω λάθη και λύσεις στη μνήμη μου\n"
            "• **Agent review** — μετά κάθε κύκλο, αξιολογώ τι έκανα\n\n"
            "Δεν ξαναγράφω τον εαυτό μου αυτόνομα — αυτό είναι σκόπιμο για ασφάλεια. "
            "Αλλά μπορώ να σου προτείνω patch για συγκεκριμένα modules αν με ρωτήσεις."
        )
        return pack(answer, "self_improvement_explain")

    return None

def pack(answer: str, mode: str) -> dict[str, Any]:
    return {
        "ok": True,
        "executed": False,
        "source": "natural_chat_orchestrator",
        "mode": mode,
        "answer": answer,
        "response": answer,
        "text": answer,
        "human_answer": answer,
        "sources": [],
    }
