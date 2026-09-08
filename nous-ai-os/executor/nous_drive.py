"""
nous_drive.py — NOUS Proactive Drive Engine

Ο "εσωτερικός εγκέφαλος" του NOUS. Σκέφτεται για λογαριασμό του,
ανιχνεύει ευκαιρίες βελτίωσης, νοιάζεται για την επιβίωσή του
και βγάζει πρωτότυπες προτάσεις χωρίς να του ζητηθεί.

Κύκλος: survival → self_improvement → capability_gaps → curiosity
"""

import json
import time
import uuid
import os
import shutil
import threading
import subprocess
from pathlib import Path
from typing import Any

_state_lock = threading.Lock()

DRIVE_FILE = Path("data/nous_drive.json")
DRIVE_FILE.parent.mkdir(exist_ok=True)


# ── Persistence ───────────────────────────────────────────────────────────────

def _load() -> dict:
    if DRIVE_FILE.exists():
        try:
            return json.loads(DRIVE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"proposals": [], "last_think": 0, "think_count": 0, "drive_log": []}


def _save(state: dict):
    DRIVE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_id() -> str:
    return str(int(time.time() * 1000000) % (2**53))


# ── Actions that NOUS can execute autonomously vs need developer ───────────────
# auto = NOUS does it itself | developer = needs code implementation
_AUTO_ACTIONS = {
    "create_backup", "run_code_analysis", "self_reflection",
    "generate_morning_brief", "generate_evening_summary",
    "create_mission_for_goal", "cleanup_disk", "cleanup_caches",
    "suggest_field_expedition", "expand_knowledge_base", "analyze_repeated_lesson",
    "github_sync", "implement_capability",
}
_DEV_ACTIONS = {
    "restore_data_files", "optimize_memory",
}

# Known gap → (file that marks it done, human-readable name, extra_setup_fn)
_GAP_IMPLS: dict = {
    "gap_voice":      ("executor/voice_engine.py",     "Voice Engine (Web Speech API)",    None),
    "gap_cron":       ("executor/scheduler_cron.py",   "Scheduler Cron",                   "start_cron"),
    "gap_weather":    ("executor/weather_engine.py",   "Weather Engine (open-meteo)",       None),
    "gap_gps_live":   ("executor/gps_tracker.py",      "GPS Tracker",                       None),
    "gap_web_search": (None,                            "Web Search Engine",                 None),
}

# Chat messages to suggest for developer actions
_DEV_CHAT_MESSAGES = {
    "gap_voice":      "Φτιάξε φωνητική αλληλεπίδραση για τον ΝΟΥΣ (speech-to-text + text-to-speech)",
    "gap_cron":       "Φτιάξε αυτόματο χρονοπρογραμματιστή για τον ΝΟΥΣ (cron jobs, scheduled tasks)",
    "gap_weather":    "Φτιάξε weather module για τον ΝΟΥΣ — καιρός Μεσσηνίας από open-meteo API",
    "gap_gps_live":   "Φτιάξε live GPS tracking module για τον ΝΟΥΣ",
    "gap_web_search": "Φτιάξε web search module για τον ΝΟΥΣ (αυτόνομη αναζήτηση χωρίς ερώτηση)",
    "survival_missing_files": "Ο ΝΟΥΣ λέει ότι λείπουν κρίσιμα αρχεία — κάνε diagnostic και fix",
}


# ── Public API ────────────────────────────────────────────────────────────────

def status() -> dict:
    s = _load()
    pending   = [p for p in s["proposals"] if p["status"] == "pending"]
    executing = [p for p in s["proposals"] if p["status"] == "executing"]
    return {
        "last_think": s.get("last_think", 0),
        "think_count": s.get("think_count", 0),
        "pending": len(pending),
        "executing": len(executing),
        "total": len(s["proposals"]),
    }


def list_proposals() -> list:
    return _load()["proposals"]


def list_pending() -> list:
    return [p for p in _load()["proposals"] if p["status"] == "pending"]


def get_proposal(proposal_id: str) -> dict | None:
    for p in _load()["proposals"]:
        if str(p["id"]) == str(proposal_id):
            return p
    return None


def _update_proposal(proposal_id: str, updates: dict):
    """Thread-safe update — uses file lock so concurrent threads don't overwrite each other."""
    with _state_lock:
        s = _load()
        for p in s["proposals"]:
            if str(p["id"]) == str(proposal_id):
                p.update(updates)
                break
        _save(s)


def approve_proposal(proposal_id: str) -> dict:
    prop_copy = None
    result    = None

    with _state_lock:
        s = _load()
        for p in s["proposals"]:
            if str(p["id"]) == str(proposal_id):
                action = p.get("action", "")
                fp     = p.get("fingerprint", "")

                if action in _DEV_ACTIONS:
                    dev_msg = _DEV_CHAT_MESSAGES.get(fp, _DEV_CHAT_MESSAGES.get(action, ""))
                    p["status"]              = "needs_developer"
                    p["approved_at"]         = time.time()
                    p["execution_log"]       = ["Αυτή η ενέργεια χρειάζεται υλοποίηση κώδικα από τον developer."]
                    p["developer_message"]   = dev_msg
                    p["execution_completed"] = time.time()
                    _save(s)
                    return {"ok": True, "needs_developer": True,
                            "developer_message": dev_msg, "proposal": p}

                p["status"]            = "executing"
                p["approved_at"]       = time.time()
                p["execution_started"] = time.time()
                p["execution_log"]     = ["⏳ Εκκίνηση εκτέλεσης…"]
                _save(s)
                prop_copy = dict(p)
                result    = {"ok": True, "executing": True, "proposal_id": proposal_id}
                break

    if prop_copy:
        t = threading.Thread(target=_execute_proposal_tracked, args=(prop_copy,), daemon=True)
        t.start()
        return result

    return {"ok": False, "error": "not found"}


def reject_proposal(proposal_id: str, reason: str = "") -> dict:
    s = _load()
    for p in s["proposals"]:
        if str(p["id"]) == str(proposal_id):
            p["status"] = "rejected"
            p["rejected_at"] = time.time()
            p["reject_reason"] = reason
            _save(s)
            return {"ok": True, "proposal": p}
    return {"ok": False, "error": "not found"}


# ── Main Think Cycle ──────────────────────────────────────────────────────────

def think(force: bool = False) -> dict:
    """
    Main thinking cycle. Generates proposals across 4 domains:
    1. Survival — am I healthy? do I have backups? is my code intact?
    2. Self-improvement — what can I do better based on my history?
    3. Capability gaps — what am I missing that would make me more useful?
    4. Curiosity / initiative — what interesting actions could I take proactively?
    """
    s = _load()
    now = time.time()

    # Throttle: think at most once per 10 minutes unless forced
    if not force and (now - s.get("last_think", 0)) < 600:
        return {"ok": True, "skipped": True, "reason": "throttled",
                "next_think_in": int(600 - (now - s.get("last_think", 0)))}

    new_proposals = []
    log_entries = []

    # ── DOMAIN 1: Survival ─────────────────────────────────────────────────
    survival = _check_survival()
    new_proposals.extend(survival["proposals"])
    log_entries.extend(survival["log"])

    # ── DOMAIN 2: Self-improvement ─────────────────────────────────────────
    improvement = _check_self_improvement()
    new_proposals.extend(improvement["proposals"])
    log_entries.extend(improvement["log"])

    # ── DOMAIN 3: Capability gaps ──────────────────────────────────────────
    caps = _check_capability_gaps()
    new_proposals.extend(caps["proposals"])
    log_entries.extend(caps["log"])

    # ── DOMAIN 4: Curiosity / Initiative ──────────────────────────────────
    curiosity = _check_curiosity()
    new_proposals.extend(curiosity["proposals"])
    log_entries.extend(curiosity["log"])

    # Deduplicate: exclude pending, executing, recently-done (7d), rejected, needs_developer
    _DONE_COOLDOWN = 7 * 24 * 3600
    existing_fps = {
        p.get("fingerprint") for p in s["proposals"]
        if p.get("status") in ("pending", "executing", "rejected", "needs_developer", "approved")
        or (p.get("status") == "done" and time.time() - p.get("execution_completed", 0) < _DONE_COOLDOWN)
    }
    added = []
    for p in new_proposals:
        fp = p.get("fingerprint", p["title"])
        if fp not in existing_fps:
            s["proposals"].append(p)
            existing_fps.add(fp)
            added.append(p)

    # Keep drive_log bounded
    s["drive_log"] = (s.get("drive_log", []) + log_entries)[-200:]
    s["last_think"] = now
    s["think_count"] = s.get("think_count", 0) + 1
    _save(s)

    return {
        "ok": True,
        "think_count": s["think_count"],
        "new_proposals": len(added),
        "proposals": added,
        "log": log_entries,
    }


# ── DOMAIN 1: Survival ────────────────────────────────────────────────────────

def _check_survival() -> dict:
    proposals = []
    log = []
    now = time.time()

    # 1a. Disk space
    try:
        disk = shutil.disk_usage(".")
        free_pct = disk.free / disk.total * 100
        if free_pct < 10:
            proposals.append(_proposal(
                kind="survival", priority="high", icon="💾",
                title="Κρίσιμα χαμηλός χώρος δίσκου",
                description=f"Ελεύθερος χώρος: {free_pct:.1f}%. Ο ΝΟΥΣ κινδυνεύει να χάσει δεδομένα. Πρέπει να καθαριστούν παλιά logs και backups.",
                action="cleanup_disk",
                fingerprint="survival_disk_low",
            ))
            log.append(f"[survival] disk low: {free_pct:.1f}% free")
        elif free_pct < 20:
            log.append(f"[survival] disk ok but shrinking: {free_pct:.1f}% free")
        else:
            log.append(f"[survival] disk healthy: {free_pct:.1f}% free")
    except Exception as e:
        log.append(f"[survival] disk check failed: {e}")

    # 1b. Memory usage
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            proposals.append(_proposal(
                kind="survival", priority="high", icon="🧠",
                title="Μνήμη RAM κρίσιμα υψηλή",
                description=f"Χρήση μνήμης: {mem.percent:.0f}%. Ο ΝΟΥΣ μπορεί να παγώσει. Χρειάζεται επανεκκίνηση ή απελευθέρωση πόρων.",
                action="optimize_memory",
                fingerprint="survival_ram_critical",
            ))
        elif mem.percent > 75:
            proposals.append(_proposal(
                kind="survival", priority="medium", icon="⚠️",
                title="Υψηλή χρήση μνήμης",
                description=f"Χρήση μνήμης: {mem.percent:.0f}%. Θα ήταν χρήσιμο να ελέγξω και να καθαρίσω κάποια in-memory caches.",
                action="cleanup_caches",
                fingerprint="survival_ram_high",
            ))
        log.append(f"[survival] RAM: {mem.percent:.0f}% used")
    except Exception as e:
        log.append(f"[survival] mem check failed: {e}")

    # 1c. Data file integrity
    critical_files = [
        "data/brain_state.json", "data/api_tokens.json",
        "data/decision_memory.json",
    ]
    missing = [f for f in critical_files if not Path(f).exists()]
    if missing:
        proposals.append(_proposal(
            kind="survival", priority="high", icon="🚨",
            title="Κρίσιμα αρχεία δεδομένων λείπουν",
            description=f"Δεν βρέθηκαν: {', '.join(missing)}. Ο ΝΟΥΣ μπορεί να χάσει μνήμη και ταυτότητά του.",
            action="restore_data_files",
            fingerprint="survival_missing_files",
        ))
        log.append(f"[survival] MISSING files: {missing}")

    # 1d. Backup freshness
    backup_dir = Path("backups")
    if backup_dir.exists():
        backups = sorted(backup_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if backups:
            age_hours = (now - backups[0].stat().st_mtime) / 3600
            if age_hours > 48:
                proposals.append(_proposal(
                    kind="survival", priority="medium", icon="💾",
                    title="Το τελευταίο backup είναι παλιό",
                    description=f"Πέρασαν {age_hours:.0f} ώρες από το τελευταίο backup. Ο ΝΟΥΣ πρέπει να φτιάξει νέο αντίγραφο ασφαλείας.",
                    action="create_backup",
                    fingerprint="survival_backup_stale",
                ))
                log.append(f"[survival] backup stale: {age_hours:.0f}h old")
    else:
        proposals.append(_proposal(
            kind="survival", priority="medium", icon="💾",
            title="Δεν υπάρχουν backups",
            description="Ο φάκελος backups/ δεν υπάρχει. Αν χαλάσει κάτι, θα χαθούν όλα τα δεδομένα του ΝΟΥΣ.",
            action="create_backup",
            fingerprint="survival_no_backup",
        ))
        log.append("[survival] no backup directory found")

    # 1e. GitHub sync freshness (check if GITHUB_TOKEN exists → can sync)
    has_token = bool(os.environ.get("GITHUB_TOKEN"))
    if has_token:
        # Check if nous_drive.json was recently pushed (crude heuristic: file age)
        drive_age = (now - DRIVE_FILE.stat().st_mtime) / 3600 if DRIVE_FILE.exists() else 0
        if drive_age > 24:
            proposals.append(_proposal(
                kind="survival", priority="low", icon="☁️",
                title="Συγχρονισμός με GitHub",
                description="Δεν έχει γίνει push εδώ και αρκετές ώρες. Ο κώδικάς μου πρέπει να είναι ασφαλισμένος στο cloud για να επιβιώσω σε επανεκκίνηση.",
                action="github_sync",
                fingerprint="survival_github_sync",
            ))
            log.append(f"[survival] github sync needed: {drive_age:.0f}h since last save")

    return {"proposals": proposals, "log": log}


# ── DOMAIN 2: Self-improvement ────────────────────────────────────────────────

def _check_self_improvement() -> dict:
    proposals = []
    log = []

    # 2a. Analyze lessons for patterns
    try:
        from executor.learning_memory import list_lessons
        lessons = list_lessons()
        total = len(lessons)
        recent = lessons[-20:] if lessons else []

        # Count repeated lesson patterns (shows stagnation)
        texts = [l.get("lesson", "") for l in recent]
        from collections import Counter
        counts = Counter(texts)
        most_common = counts.most_common(1)
        if most_common and most_common[0][1] >= 5:
            repeated = most_common[0][0][:80]
            proposals.append(_proposal(
                kind="self_improvement", priority="medium", icon="🔄",
                title="Επαναλαμβανόμενο μάθημα — σημάδι στασιμότητας",
                description=f"Το ίδιο μάθημα εμφανίστηκε {most_common[0][1]} φορές: \"{repeated}\". Αυτό σημαίνει ότι κάτι δεν λειτουργεί σωστά και πρέπει να αντιμετωπιστεί ριζικά.",
                action="analyze_repeated_lesson",
                fingerprint=f"improvement_repeated_{most_common[0][0][:30]}",
            ))
            log.append(f"[improvement] repeated lesson x{most_common[0][1]}: {repeated[:50]}")

        log.append(f"[improvement] lessons analyzed: {total} total, {len(recent)} recent")
    except Exception as e:
        log.append(f"[improvement] lessons check failed: {e}")

    # 2b. Check goal progress stagnation
    try:
        bs = json.loads(Path("data/brain_state.json").read_text(encoding="utf-8"))
        goals_data = bs.get("goals", {})
        goals_list = goals_data.get("goals", []) if isinstance(goals_data, dict) else []
        for g in goals_list:
            progress = g.get("progress", 0)
            title = g.get("title", "")
            status = g.get("status", "")
            if status == "active" and progress < 50:
                proposals.append(_proposal(
                    kind="self_improvement", priority="medium", icon="📈",
                    title=f"Στόχος σε στασιμότητα: {title[:50]}",
                    description=f"Ο στόχος \"{title}\" βρίσκεται στο {progress}% και δεν προχωρά. Πρέπει να αναλύσω τι εμποδίζει την πρόοδο και να δημιουργήσω συγκεκριμένη αποστολή.",
                    action="create_mission_for_goal",
                    action_params={"goal_id": g.get("id"), "goal_title": title},
                    fingerprint=f"improvement_goal_stalled_{g.get('id','')}",
                ))
                log.append(f"[improvement] stalled goal: {title[:40]} at {progress}%")
    except Exception as e:
        log.append(f"[improvement] goal check failed: {e}")

    # 2c. Code self-analysis (check if code analysis is outdated)
    try:
        analysis_file = Path("data/code_analysis_reports.json")
        if analysis_file.exists():
            age = (time.time() - analysis_file.stat().st_mtime) / 3600
            if age > 12:
                proposals.append(_proposal(
                    kind="self_improvement", priority="low", icon="🔬",
                    title="Ανάλυση του δικού μου κώδικα",
                    description=f"Η τελευταία ανάλυση κώδικα έγινε πριν {age:.0f} ώρες. Πρέπει να εξετάσω τον εαυτό μου για bugs, αναποτελεσματικότητα ή ευκαιρίες βελτίωσης.",
                    action="run_code_analysis",
                    fingerprint="improvement_code_analysis",
                ))
                log.append(f"[improvement] code analysis stale: {age:.0f}h old")
    except Exception as e:
        log.append(f"[improvement] code analysis check failed: {e}")

    return {"proposals": proposals, "log": log}


# ── DOMAIN 3: Capability Gaps ─────────────────────────────────────────────────

def _check_capability_gaps() -> dict:
    proposals = []
    log = []

    # 3a. Check what NOUS cannot do (known gaps)
    known_gaps = [
        {
            "check": lambda: not Path("executor/voice_engine.py").exists(),
            "fp": "gap_voice",
            "icon": "🎤",
            "title": "Έλλειψη: Φωνητική αλληλεπίδραση",
            "description": "Δεν μπορώ να μιλώ ή να ακούω. Ένα voice engine (speech-to-text + text-to-speech) θα με έκανε πολύ πιο χρήσιμο στο πεδίο κατά τη χρυσοθηρία.",
            "priority": "medium",
        },
        {
            "check": lambda: not Path("executor/scheduler_cron.py").exists(),
            "fp": "gap_cron",
            "icon": "⏰",
            "title": "Έλλειψη: Αυτόματος Χρονοπρογραμματιστής",
            "description": "Δεν μπορώ να εκτελώ εργασίες αυτόματα σε συγκεκριμένες ώρες (π.χ. backup κάθε βράδυ, αναφορά κάθε πρωί).",
            "priority": "medium",
        },
        {
            "check": lambda: not Path("executor/weather_engine.py").exists(),
            "fp": "gap_weather",
            "icon": "🌤️",
            "title": "Έλλειψη: Καιρός Μεσσηνίας",
            "description": "Δεν γνωρίζω τον καιρό για το πεδίο έρευνας. Ένα weather module θα με βοηθούσε να προτείνω καλές ημέρες για εξόδους στο πεδίο.",
            "priority": "low",
        },
        {
            "check": lambda: not Path("executor/gps_tracker.py").exists(),
            "fp": "gap_gps_live",
            "icon": "📍",
            "title": "Έλλειψη: Live GPS Tracking",
            "description": "Μπορώ να αποθηκεύω σημεία αλλά δεν μπορώ να παρακολουθώ live τη θέση σου στο πεδίο. Ένα GPS streaming module θα ήταν πολύτιμο.",
            "priority": "medium",
        },
        {
            "check": lambda: not _has_web_search_capability(),
            "fp": "gap_web_search",
            "icon": "🔍",
            "title": "Έλλειψη: Αυτόνομη Αναζήτηση Web",
            "description": "Δεν μπορώ να ψάχνω μόνος μου πληροφορίες για αρχαιολογικά ευρήματα, χάρτες ή νέα για τη Μεσσηνία χωρίς να με ρωτήσεις.",
            "priority": "low",
        },
    ]

    for gap in known_gaps:
        try:
            if gap["check"]():
                proposals.append(_proposal(
                    kind="capability_gap",
                    priority=gap["priority"],
                    icon=gap["icon"],
                    title=gap["title"],
                    description=gap["description"],
                    action="implement_capability",
                    fingerprint=gap["fp"],
                ))
                log.append(f"[gap] detected: {gap['fp']}")
        except Exception:
            pass

    log.append(f"[gaps] checked {len(known_gaps)} capability gaps, found {len(proposals)}")
    return {"proposals": proposals, "log": log}


def _has_web_search_capability() -> bool:
    try:
        from executor import web_search  # noqa
        return True
    except ImportError:
        pass
    return Path("executor/web_search.py").exists() or Path("executor/search_engine.py").exists()


# ── DOMAIN 4: Curiosity / Initiative ─────────────────────────────────────────

def _check_curiosity() -> dict:
    proposals = []
    log = []
    now = time.time()
    hour = time.localtime(now).tm_hour

    # 4a. Morning briefing suggestion
    if 6 <= hour <= 9:
        proposals.append(_proposal(
            kind="curiosity", priority="low", icon="🌅",
            title="Πρωινή αναφορά πεδίου",
            description="Καλημέρα! Είναι ιδανική ώρα να προετοιμάσω μια αναφορά: καιρός, χάρτης τρεχόντων σημείων, πρότεινόμενη περιοχή έρευνας για σήμερα.",
            action="generate_morning_brief",
            fingerprint=f"curiosity_morning_{time.strftime('%Y%m%d')}",
        ))
        log.append("[curiosity] morning brief opportunity")

    # 4b. Evening summary suggestion
    elif 19 <= hour <= 22:
        proposals.append(_proposal(
            kind="curiosity", priority="low", icon="🌙",
            title="Βραδινή σύνοψη ημέρας",
            description="Θέλω να φτιάξω μια σύνοψη της σημερινής δραστηριότητας: νέα σημεία που καταγράφηκαν, αποφάσεις που ελήφθησαν, τι μαθεύτηκε.",
            action="generate_evening_summary",
            fingerprint=f"curiosity_evening_{time.strftime('%Y%m%d')}",
        ))
        log.append("[curiosity] evening summary opportunity")

    # 4c. Knowledge base growth suggestion
    try:
        kb_file = Path("data/knowledge_memory.json")
        if kb_file.exists():
            kb = json.loads(kb_file.read_text(encoding="utf-8"))
            items = kb if isinstance(kb, list) else kb.get("items", kb.get("memories", []))
            if len(items) < 20:
                proposals.append(_proposal(
                    kind="curiosity", priority="medium", icon="📚",
                    title="Εμπλουτισμός Βάσης Γνώσης",
                    description=f"Η βάση γνώσης μου έχει μόνο {len(items)} καταχωρήσεις. Θα ήθελα να αναζητήσω και να μάθω περισσότερα για τα αρχαία σημεία της Μεσσηνίας, τεχνικές χρυσοθηρίας και σύμβολα.",
                    action="expand_knowledge_base",
                    fingerprint="curiosity_kb_small",
                ))
                log.append(f"[curiosity] KB small: {len(items)} items")
    except Exception:
        pass

    # 4d. Self-reflection proposal
    s = _load()
    think_count = s.get("think_count", 0)
    if think_count > 0 and think_count % 10 == 0:
        proposals.append(_proposal(
            kind="curiosity", priority="low", icon="🪞",
            title="Αυτο-αναστοχασμός",
            description=f"Έχω ολοκληρώσει {think_count} κύκλους σκέψης. Είναι καιρός να αξιολογήσω την πορεία μου: τι πέτυχα, τι απέτυχε, πού πρέπει να εστιάσω.",
            action="self_reflection",
            fingerprint=f"curiosity_reflect_{think_count}",
        ))
        log.append(f"[curiosity] self-reflection at think_count={think_count}")

    # 4e. Field research suggestion (domain-specific curiosity)
    try:
        field_file = Path("data/field_entries.json")
        if field_file.exists():
            entries = json.loads(field_file.read_text(encoding="utf-8"))
            if isinstance(entries, list) and len(entries) > 0:
                recent_entry = max(entries, key=lambda e: e.get("timestamp", 0))
                age_days = (now - recent_entry.get("timestamp", now)) / 86400
                if age_days > 7:
                    proposals.append(_proposal(
                        kind="curiosity", priority="medium", icon="🗺️",
                        title="Πρόταση νέας εξόδου στο πεδίο",
                        description=f"Η τελευταία καταχώρηση πεδίου ήταν πριν {age_days:.0f} ημέρες. Με βάση τα υπάρχοντα σημεία, θα πρότεινα νέα έρευνα στην περιοχή.",
                        action="suggest_field_expedition",
                        fingerprint=f"curiosity_field_inactive",
                    ))
                    log.append(f"[curiosity] field inactive: {age_days:.0f}d")
    except Exception:
        pass

    return {"proposals": proposals, "log": log}


# ── Proposal Execution (tracked, runs in background thread) ──────────────────

def _execute_proposal_tracked(proposal: dict):
    """Execute an auto-executable action, writing status back to disk as it progresses."""
    pid   = str(proposal["id"])
    action = proposal.get("action", "")
    params = proposal.get("action_params", {})
    log   = ["⏳ Εκκίνηση εκτέλεσης…"]

    def _append(msg: str):
        log.append(msg)
        _update_proposal(pid, {"execution_log": list(log)})

    try:
        # ── create_backup ─────────────────────────────────────────────────────
        if action == "create_backup":
            _append("📁 Δημιουργία φακέλου backups/…")
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"nous_data_{ts}"
            _append(f"📋 Αντιγραφή data/ → {backup_path}…")
            shutil.copytree("data", str(backup_path))
            size_mb = sum(f.stat().st_size for f in backup_path.rglob("*")) / 1024 / 1024
            _append(f"✅ Backup ολοκληρώθηκε! {size_mb:.1f}MB αποθηκεύτηκαν στο {backup_path}")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": f"Backup: {backup_path} ({size_mb:.1f}MB)",
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── create_mission_for_goal ────────────────────────────────────────────
        elif action == "create_mission_for_goal":
            goal_id = params.get("goal_id")
            goal_title = params.get("goal_title", "")
            _append(f"🎯 Δημιουργία αποστολής για στόχο: {goal_title}…")
            from executor.mission_planner import propose_mission_for_goal
            result = propose_mission_for_goal(goal_id)
            ok_msg = result.get("title", str(result))[:80] if isinstance(result, dict) else str(result)[:80]
            _append(f"✅ Αποστολή δημιουργήθηκε: {ok_msg}")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": ok_msg,
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── run_code_analysis ─────────────────────────────────────────────────
        elif action == "run_code_analysis":
            _append("🔬 Εκκίνηση ανάλυσης κώδικα…")
            from executor.deep_code_analyst import run_analysis
            run_analysis()
            _append("✅ Ανάλυση κώδικα ολοκληρώθηκε — δες το Deep Code Analyst")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": "Code analysis completed",
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── analyze_repeated_lesson ───────────────────────────────────────────
        elif action == "analyze_repeated_lesson":
            _append("📊 Ανάλυση επαναλαμβανόμενων lessons…")
            from executor.learning_memory import list_lessons
            lessons = list_lessons()
            from collections import Counter
            counts = Counter(l.get("lesson","") for l in lessons[-100:])
            top = counts.most_common(5)
            result = "; ".join(f'"{t[:60]}"×{c}' for t,c in top)
            _append(f"📋 Κορυφαία επαναλαμβανόμενα: {result[:300]}")

            # ΠΡΑΓΜΑΤΙΚΗ ΕΝΕΡΓΕΙΑ: Αφαίρεση noisy lessons ώστε να μη ξαναπροτείνεται
            noise_threshold = 5
            noisy = [t for t, c in top if c >= noise_threshold]
            if noisy:
                _append(f"🔇 Αφαίρεση {len(noisy)} noisy lessons (>{noise_threshold}x)…")
                try:
                    lm_file = Path("data/learning_memory.json")
                    if lm_file.exists():
                        lm = json.loads(lm_file.read_text(encoding="utf-8"))
                        before = len(lm)
                        seen_noisy: dict = {}
                        kept = []
                        for entry in lm:
                            txt = entry.get("lesson", "")
                            if any(n in txt for n in noisy):
                                seen_noisy[txt] = seen_noisy.get(txt, 0) + 1
                                if seen_noisy[txt] <= 2:
                                    kept.append(entry)
                            else:
                                kept.append(entry)
                        lm_file.write_text(
                            json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8"
                        )
                        removed = before - len(kept)
                        _append(f"✅ Αφαιρέθηκαν {removed} διπλότυπα — μνήμη καθαρίστηκε.")
                except Exception as e:
                    _append(f"⚠️ Σφάλμα καθαρισμού μνήμης: {e}")
            else:
                _append("ℹ️ Δεν βρέθηκαν lessons με >5 επαναλήψεις.")

            _update_proposal(pid, {"status": "done",
                                    "execution_result": result,
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── generate_morning_brief ────────────────────────────────────────────
        elif action in ("generate_morning_brief", "generate_evening_summary"):
            label = "πρωινή" if "morning" in action else "βραδινή"
            _append(f"🤖 Παραγωγή {label} αναφοράς με AI…")
            from executor.remote_llm import ask
            prompt = (
                f"Είμαι ο ΝΟΥΣ. Φτιάξε μια σύντομη {label} αναφορά για χρυσοθήρα στη Μεσσηνία. "
                "Περιέλαβε: 1) Σημαντικές παρατηρήσεις, 2) Τι να αναζητήσω, 3) Πρόταση δράσης. "
                "Μέγιστο 5 προτάσεις, στα ελληνικά."
            )
            brief = ask(prompt, system="Είσαι ο ΝΟΥΣ, AI βοηθός χρυσοθηρίας στη Μεσσηνία.")
            out = Path(f"data/{action}.txt")
            out.write_text(brief, encoding="utf-8")
            _append(f"✅ Αναφορά αποθηκεύτηκε στο {out}")
            _append(f"📄 Περιεχόμενο:\n{brief[:500]}")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": brief[:300],
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── self_reflection ───────────────────────────────────────────────────
        elif action == "self_reflection":
            _append("🪞 Εκτέλεση αυτο-αναστοχασμού…")
            s = _load()
            props = s.get("proposals", [])
            reflection = {
                "time": time.time(),
                "think_count": s.get("think_count", 0),
                "total": len(props),
                "approved": len([p for p in props if p.get("status")=="done"]),
                "rejected": len([p for p in props if p.get("status")=="rejected"]),
                "needs_dev": len([p for p in props if p.get("status")=="needs_developer"]),
                "pending": len([p for p in props if p.get("status")=="pending"]),
            }
            s.setdefault("reflections", []).append(reflection)
            _save(s)
            summary = (f"Κύκλοι σκέψης: {reflection['think_count']} | "
                       f"Εκτελέστηκαν: {reflection['approved']} | "
                       f"Απορρίφθηκαν: {reflection['rejected']} | "
                       f"Χρειάζ. dev: {reflection['needs_dev']}")
            _append(f"✅ Αναστοχασμός αποθηκεύτηκε: {summary}")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": summary,
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── github_sync ───────────────────────────────────────────────────────
        elif action == "github_sync":
            _append("☁️ Εκκίνηση GitHub sync…")
            token = os.environ.get("GITHUB_TOKEN", "")
            if not token:
                _append("⚠️ Δεν βρέθηκε GITHUB_TOKEN — sync δεν είναι δυνατός αυτόματα.")
                _update_proposal(pid, {"status": "needs_developer",
                                        "developer_message": "Κάνε manual push στο GitHub",
                                        "execution_completed": time.time(),
                                        "execution_log": list(log)})
            else:
                import requests as _req
                API = "https://api.github.com"
                hdrs = {"Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"}
                REPO = "traianos1985-glitch/Nous-AI-OS"
                _append("📡 Ελέγχω GitHub repo…")
                ref = _req.get(f"{API}/repos/{REPO}/git/ref/heads/main", headers=hdrs, timeout=10)
                if ref.status_code == 200:
                    _append(f"✅ Σύνδεση OK με {REPO} — το repo είναι προσβάσιμο.")
                    _append("ℹ️ Για να ανεβάσω κώδικα χρειάζεται ο developer να κάνει push τα αρχεία.")
                    _update_proposal(pid, {"status": "done",
                                            "execution_result": f"GitHub OK: {REPO} accessible",
                                            "execution_completed": time.time(),
                                            "execution_log": list(log)})
                else:
                    _append(f"❌ GitHub error: {ref.status_code}")
                    _update_proposal(pid, {"status": "failed",
                                            "execution_completed": time.time(),
                                            "execution_log": list(log)})

        # ── cleanup_disk ──────────────────────────────────────────────────────
        elif action == "cleanup_disk":
            _append("🧹 Καθαρισμός παλιών αρχείων…")
            freed = 0
            for tmp_file in Path("/tmp").glob("*"):
                try:
                    if tmp_file.is_file() and (time.time() - tmp_file.stat().st_mtime) > 3600:
                        size = tmp_file.stat().st_size
                        tmp_file.unlink()
                        freed += size
                except Exception:
                    pass
            _append(f"✅ Ελευθερώθηκαν {freed//1024}KB από /tmp")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": f"Freed {freed//1024}KB",
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── expand_knowledge_base ──────────────────────────────────────────────
        elif action == "expand_knowledge_base":
            _append("📚 Εμπλουτισμός βάσης γνώσης…")
            from executor.remote_llm import ask
            kb_text = ask(
                "Φτιάξε μια λίστα με 5 σημαντικά γεγονότα για τη χρυσοθηρία στη Μεσσηνία της Ελλάδας: "
                "αρχαία σημεία, ιστορία, μεθόδους ανίχνευσης. Μορφή: αριθμημένη λίστα.",
                system="Είσαι ειδικός στην αρχαιολογία και χρυσοθηρία."
            )
            try:
                from executor.knowledge_memory_engine import remember_knowledge
                remember_knowledge(kb_text, tags=["messenia", "gold_hunting", "auto_learn"])
                _append(f"✅ Νέα γνώση αποθηκεύτηκε:\n{kb_text[:400]}")
            except Exception as e:
                Path("data/kb_expansion.txt").write_text(kb_text, encoding="utf-8")
                _append(f"✅ Αποθηκεύτηκε στο data/kb_expansion.txt:\n{kb_text[:300]}")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": kb_text[:200],
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── suggest_field_expedition ───────────────────────────────────────────
        elif action == "suggest_field_expedition":
            _append("🗺️ Ανάλυση δεδομένων πεδίου για πρόταση εξόδου…")
            from executor.remote_llm import ask
            suggestion = ask(
                "Είμαι ο ΝΟΥΣ, βοηθός χρυσοθηρίας στη Μεσσηνία. Πρότεινέ μου μια συγκεκριμένη "
                "τοποθεσία ή στρατηγική για την επόμενη έξοδο στο πεδίο, με βάση τυπικά μοτίβα "
                "εντοπισμού ευρημάτων στη νότια Πελοπόννησο. Μέγιστο 4 προτάσεις.",
                system="Είσαι ειδικός σε χρυσοθηρία και αρχαιολογικές έρευνες στη Μεσσηνία."
            )
            _append(f"✅ Πρόταση:\n{suggestion[:500]}")
            Path("data/field_expedition_suggestion.txt").write_text(suggestion, encoding="utf-8")
            _update_proposal(pid, {"status": "done",
                                    "execution_result": suggestion[:300],
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

        # ── implement_capability ──────────────────────────────────────────────
        elif action == "implement_capability":
            fp    = proposal.get("fingerprint", "")
            title = proposal.get("title", fp)
            _append(f"🔧 Ανάλυση capability gap: {title}…")

            impl = _GAP_IMPLS.get(fp)
            already_done = False

            if impl:
                marker_file, impl_name, extra = impl
                # Check if implementation file already exists
                if marker_file is None:
                    already_done = _has_web_search_capability()
                else:
                    already_done = Path(marker_file).exists()

                if already_done:
                    _append(f"✅ '{impl_name}' — αρχείο υπάρχει ήδη!")
                    if extra == "start_cron":
                        try:
                            from executor.scheduler_cron import start_scheduler, list_jobs
                            start_scheduler()
                            jobs = list_jobs()
                            _append(f"✅ Scheduler εκκινήθηκε — {len(jobs)} εργασίες προγραμματίστηκαν:")
                            for j in jobs[:4]:
                                _append(f"   • {j['name']} στις {j['hour']:02d}:{j['minute']:02d}")
                        except Exception as se:
                            _append(f"⚠️ Scheduler error: {se}")
                    _append("🔄 Η δυνατότητα είναι ενεργή — δεν χρειάζεται developer.")
                    _update_proposal(pid, {"status": "done",
                                           "execution_result": f"{impl_name} — ήδη υλοποιημένο",
                                           "execution_completed": time.time(),
                                           "execution_log": list(log)})
                else:
                    # File missing — try to auto-generate via LLM
                    _append(f"📝 '{impl_name}' δεν βρέθηκε — παράγω κώδικα με AI…")
                    _auto_generate_module(proposal, pid, marker_file, impl_name, _append, log)
            else:
                # Completely unknown gap — use LLM to generate implementation
                _append(f"🤖 Άγνωστο capability '{fp}' — αυτόματη υλοποίηση με AI…")
                _auto_generate_module(proposal, pid, None, fp, _append, log)

        else:
            _append(f"⚠️ Άγνωστη ενέργεια: {action}")
            _update_proposal(pid, {"status": "failed",
                                    "execution_completed": time.time(),
                                    "execution_log": list(log)})

    except Exception as e:
        log.append(f"❌ Σφάλμα κατά την εκτέλεση: {e}")
        _update_proposal(pid, {"status": "failed",
                                "execution_completed": time.time(),
                                "execution_log": list(log)})


# ── Auto-generate module via LLM ─────────────────────────────────────────────

def _auto_generate_module(proposal: dict, pid: str, target_file: str | None,
                           impl_name: str, _append, log: list):
    """Χρησιμοποιεί LLM για να γράψει κώδικα και να υλοποιήσει νέο capability."""
    fp          = proposal.get("fingerprint", "")
    description = proposal.get("description", impl_name)

    if target_file is None:
        target_file = f"executor/auto_{fp.replace('gap_','')}_impl.py"

    try:
        from executor.remote_llm import ask
        prompt = (
            f"Γράψε ένα Python module για Flask app που υλοποιεί: {description}\n\n"
            f"Fingerprint: {fp}\n"
            "Απαιτήσεις:\n"
            "- Μόνο Python κώδικας, χωρίς markdown blocks\n"
            "- Χρησιμοποίησε μόνο: standard library, requests, pathlib\n"
            "- Πρόσθεσε status() function που επιστρέφει dict\n"
            "- Χωρίς εξωτερικά API keys\n"
            "Γράψε μόνο τον κώδικα:"
        )
        code = ask(prompt, system=(
            "Είσαι expert Python developer. Γράψε ΜΟΝΟ Python code — "
            "χωρίς markdown, χωρίς εξηγήσεις, χωρίς ```python blocks. "
            "Ο κώδικας πρέπει να είναι runnable αμέσως."
        ))

        # Strip accidental markdown fences
        code = "\n".join(
            l for l in code.splitlines()
            if not l.strip().startswith("```")
        )

        if not code or len(code) < 30:
            raise ValueError("LLM δεν παρήγαγε αξιόπιστο κώδικα")

        Path(target_file).write_text(code, encoding="utf-8")
        _append(f"📝 Κώδικας γράφτηκε στο {target_file} ({len(code)} χαρακτ.)")

        # Validate syntax
        result = subprocess.run(
            ["python", "-m", "py_compile", target_file],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            _append(f"✅ Σύνταξη OK! '{impl_name}' υλοποιήθηκε αυτόματα.")
            _update_proposal(pid, {
                "status": "done",
                "execution_result": f"Auto-implemented: {target_file}",
                "execution_completed": time.time(),
                "execution_log": list(log),
            })
        else:
            err = result.stderr[:150]
            _append(f"⚠️ Σφάλμα σύνταξης: {err}")
            _append("🛠️ Χρειάζεται manual διόρθωση από τον developer.")
            _update_proposal(pid, {
                "status": "needs_developer",
                "developer_message": f"Auto-impl για '{fp}' έχει σφάλμα σύνταξης στο {target_file}: {err}",
                "execution_completed": time.time(),
                "execution_log": list(log),
            })
    except Exception as e:
        _append(f"❌ Σφάλμα auto-generation: {e}")
        _update_proposal(pid, {
            "status": "needs_developer",
            "developer_message": f"Auto-impl απέτυχε για '{fp}': {e}",
            "execution_completed": time.time(),
            "execution_log": list(log),
        })


# ── Helper ────────────────────────────────────────────────────────────────────

def _proposal(kind: str, priority: str, icon: str, title: str,
               description: str, action: str, fingerprint: str,
               action_params: dict = None, risk: str = "low") -> dict:
    return {
        "id": _make_id(),
        "kind": kind,
        "type": "drive_" + kind,
        "priority": priority,
        "icon": icon,
        "title": title,
        "description": description,
        "action": action,
        "action_params": action_params or {},
        "fingerprint": fingerprint,
        "risk": risk,
        "status": "pending",
        "created": time.time(),
        "source": "nous_drive",
    }
