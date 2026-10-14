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
        "τι μπορείς", "τι μπορεις",
        "κατάσταση", "κατασταση", "status",
        "missions", "αποστολές", "αποστολες",
        "στόχοι", "στοχοι", "goals",
        "τι τρέχει", "τι τρεχει",
        "τι γίνεται", "τι γινεται",
        "πρόοδος", "προοδος", "progress",
        "έλεγχος υγείας", "ελεγχος υγειας", "health check",
        "υγεία συστήματος", "υγεια συστηματος",
        "όλα καλά", "ολα καλα", "όλα εντάξει", "ολα ενταξει",
        "πώς είναι το σύστημα", "πως ειναι το συστημα",
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


def pack(answer: str, mode: str, ok: bool = True, executed: bool = False, **extra) -> dict[str, Any]:
    out = {
        "ok": ok,
        "source": "natural_chat_orchestrator",
        "mode": mode,
        "answer": answer,
        "response": answer,
        "text": answer,
        "human_answer": answer,
        "sources": [],
        "executed": executed,
    }
    out.update(extra)
    return out


def natural_chat_answer(message: str) -> dict[str, Any] | None:
    m = norm(message)

    if any(x in m for x in ["με λένε", "με λενε", "εμένα με λένε", "εμενα με λενε"]):
        return pack("Χάρηκα! Εμένα μπορείς να με λες ΝΟΥΣ. Είμαι ο προσωπικός σου AI βοηθός μέσα στο NOUS AI OS.", "identity")

    if any(x in m for x in ["εσένα", "εσενα", "πως σε λένε", "πώς σε λένε", "πως σε λενε", "ποιος είσαι", "ποιος εισαι"]):
        return pack("Εμένα με λένε ΝΟΥΣ. Είμαι ο προσωπικός σου AI βοηθός για συζήτηση, κώδικα, έρευνα, έγγραφα, μνήμη και αποστολές. Ρώτα με ό,τι θέλεις στα ελληνικά!", "identity")

    if any(x in m for x in ["τι μπορείς", "τι μπορεις", "τι κάνεις εσύ", "τι κανεις εσυ", "βοήθεια", "βοηθεια", "help"]):
        answer = (
            "Μπορώ να σε βοηθήσω με:\n"
            "• **Φυσική συζήτηση** — ρώτα με ό,τι θέλεις στα ελληνικά\n"
            "• **Κώδικα** — ανάλυση, debug, βελτίωση\n"
            "• **Αναζήτηση internet** — πες «ψάξε για...»\n"
            "• **Έγγραφα** — ανέβασε PDF/Word και ρώτα γι' αυτό\n"
            "• **Μνήμη** — θυμάμαι τις συνομιλίες μας\n"
            "• **Αποστολές** — γράψε /plan <στόχος> για να δημιουργήσω αποστολή\n"
            "• **Κατάσταση** — πες «κατάσταση» ή «έλεγχος υγείας»"
        )
        return pack(answer, "capabilities")

    if any(x in m for x in ["τι κάνεις", "τι κανεις", "πως είσαι", "πώς είσαι", "πως εισαι"]):
        return pack("Είμαι εδώ και λειτουργώ κανονικά! Πες μου τι θέλεις να δούμε.", "normal_chat")

    if any(x in m for x in ["καλημέρα", "καλημερα", "καλησπέρα", "καλησπερα", "γεια", "γειά", "hello", "hi"]):
        return pack("Γεια σου! Είμαι έτοιμος. Τι θέλεις να δούμε;", "normal_chat")

    # Κατάσταση / υγεία — expanded natural phrases
    if any(x in m for x in [
        "κατάσταση", "κατασταση", "status", "τι τρέχει", "τι τρεχει",
        "τι γίνεται", "τι γινεται", "πρόοδος", "προοδος", "progress",
        "πώς πάει", "πως παει", "τι έχουμε", "τι εχουμε",
        "έλεγχος υγείας", "ελεγχος υγειας", "health check", "project health",
        "υγεία συστήματος", "υγεια συστηματος", "υγεία", "υγεια",
        "όλα καλά", "ολα καλα", "όλα εντάξει", "ολα ενταξει",
        "πώς είναι το σύστημα", "πως ειναι το συστημα",
    ]):
        return pack(_system_status_answer(), "system_status")

    if any(x in m for x in [
        "missions", "αποστολές", "αποστολες", "αποστολη", "αποστολή",
        "πόσες αποστολές", "ποσες αποστολες", "τι αποστολές", "τι αποστολες",
    ]):
        return pack(_missions_answer(), "missions_list")

    if any(x in m for x in [
        "στόχοι", "στοχοι", "goals", "στόχος", "στοχος",
        "τι στόχους", "τι στοχους", "ποιοι στόχοι", "ποιοι στοχοι",
    ]):
        return pack(_goals_answer(), "goals_list")

    mission_triggers = [
        "φτιάξε αποστολή", "φτιαξε αποστολη", "δημιούργησε αποστολή", "δημιουργησε αποστολη",
        "κάνε αποστολή", "κανε αποστολη", "νέα αποστολή", "νεα αποστολη",
        "θέλω αποστολή", "θελω αποστολη", "create mission", "new mission",
    ]
    if any(x in m for x in mission_triggers):
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

    return None
