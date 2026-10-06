from __future__ import annotations

import re
import json
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
    try:
        from executor.goal_system import goal_status
        from executor.mission_system import mission_status, pending_approvals
        from executor.operator_approval import list_approvals

        goals = goal_status()
        missions = mission_status()
        mission_approvals = pending_approvals()
        operator_approvals = list_approvals(status="pending")
        approval_count = mission_approvals["count"] + len(operator_approvals)
    except Exception:
        return "Δεν μπόρεσα να διαβάσω την τρέχουσα κατάσταση του συστήματος."

    return "\n".join([
        "**Κατάσταση NOUS AI OS**",
        "",
        f"• Αποστολές: {missions['total']} συνολικά — {missions['active']} ενεργές, {missions['done']} ολοκληρωμένες, {missions['blocked']} μπλοκαρισμένες",
        f"• Στόχοι: {goals['total']} συνολικά — {goals['active']} ενεργοί",
        f"• Εκκρεμείς εγκρίσεις: {approval_count}",
    ])


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
    from executor.goal_system import list_goals

    goals = list_goals()
    if not goals:
        return "Δεν υπάρχουν καταγεγραμμένοι στόχοι ακόμα. Μπορείς να δημιουργήσεις έναν γράφοντας «Δημιούργησε στόχο: …»."

    lines = [f"**Στόχοι** ({len(goals)} συνολικά):", ""]
    lines.extend(f"🎯 {goal.get('title', 'Χωρίς τίτλο')}" for goal in goals[:8])
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

    goal_match = re.match(
        r"^(?:δημιούργησε|δημιουργησε|βάλε|βαλε|πρόσθεσε|προσθεσε|create)\s+(?:(?:έναν?|a)\s+)?(?:στόχο|στοχο|goal)\s*[:\-]?\s*(.+)$",
        message,
        re.IGNORECASE,
    )
    if goal_match:
        title = goal_match.group(1).strip().rstrip(";?!.·")
        if not title:
            return pack("Γράψε τον τίτλο του στόχου μετά το «Δημιούργησε στόχο:».", "goal_error", ok=False)
        try:
            from executor.goal_system import create_goal
            goal = create_goal(title)
        except Exception:
            return pack("Δεν μπόρεσα να αποθηκεύσω τον στόχο.", "goal_error", ok=False)
        if not isinstance(goal, dict) or not goal.get("id"):
            return pack("Δεν μπόρεσα να επιβεβαιώσω την αποθήκευση του στόχου.", "goal_error", ok=False)
        return pack(f"Καταχωρίστηκε ο στόχος «{goal['title']}».", "goal_created", executed=True, goal_id=str(goal["id"]))

    if re.match(
        r"^(?:κάνε|κανε|δημιούργησε|δημιουργησε|πάρε|παρε|create|make)\s+(?:(?:ένα|a|an)\s+)?(?:backup|αντίγραφο ασφαλείας)\b",
        m,
    ):
        try:
            from executor.cloud_brain_backup import create_brain_backup
            backup = create_brain_backup()
        except Exception:
            return pack("Δεν μπόρεσα να δημιουργήσω backup.", "backup_error", ok=False)
        if not backup.get("ok") or not backup.get("backup"):
            return pack("Η δημιουργία backup απέτυχε.", "backup_error", ok=False)
        return pack(f"Δημιουργήθηκε backup: `{backup['backup']}`.", "backup_created", executed=True, backup=backup["backup"])

    weather_match = re.match(
        r"^(?:τι\s+καιρό(?:\s+(?:κάνει|έχει))?|(?:ο\s+)?καιρός|καιρό|πρόγνωση(?:\s+καιρού)?|weather|forecast)\b\s*(.*)$",
        m,
        re.IGNORECASE,
    )
    if weather_match:
        location = re.sub(r"^(?:στην?|στον?|στο|σε|για|in|at|for)\s+", "", weather_match.group(1)).strip(" :,-;?!.")
        location = re.sub(r"^(?:σήμερα|αύριο|σημερα|αυριο|today|tomorrow)\s+", "", location).strip()
        try:
            from executor.weather_engine import get_weather
            weather = get_weather(location=location or None)
        except Exception:
            return pack("Δεν μπόρεσα να ανακτήσω τον καιρό αυτή τη στιγμή.", "weather_error", ok=False)
        if not weather.get("ok"):
            message = f"Δεν βρήκα την τοποθεσία «{location}»." if weather.get("error") == "location_not_found" else "Δεν μπόρεσα να ανακτήσω τον καιρό αυτή τη στιγμή."
            return pack(message, "weather_error", ok=False)
        current = weather["current"]
        answer = f"Καιρός για **{weather['location']}**: {current['description']}, {current['temp']}°C, υγρασία {current['humidity']}%, άνεμος {current['wind_kmh']} km/h."
        return pack(answer, "weather", executed=True, location=weather["location"])

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
    if re.match(
        r"^(?:φτιάξε|φτιαξε|δημιούργησε|δημιουργησε|χτίσε|χτισε|κάνε|κανε|build|create|make)\s+(?:μου\s+|a\s+|an\s+)?(?:μία?\s+|ένα\s+)?(?:web\s+)?(?:app|εφαρμογή|εφαρμογη)\b",
        m,
    ):
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

def pack(answer: str, mode: str, **extra) -> dict[str, Any]:
    return {
        "ok": extra.pop("ok", True),
        "executed": extra.pop("executed", False),
        "source": "natural_chat_orchestrator",
        "mode": mode,
        "answer": answer,
        "response": answer,
        "text": answer,
        "human_answer": answer,
        "sources": [],
        **extra,
    }
