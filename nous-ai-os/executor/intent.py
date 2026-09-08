def detect_intent(text):

    t = str(text).lower().strip()
    t = t.strip("?.!,;:·…")

    if t in ["/status", "status", "κατάσταση"]:
        return {"type": "system", "action": "status"}

    if t in ["/evolve", "evolve", "εξέλιξη"]:
        return {"type": "system", "action": "evolve"}

    if t in ["/plugins", "plugins", "plugin"] or "plugins" in t:
        return {"type": "tool", "action": "plugin"}

    if t in ["/memory", "memory", "μνήμη"] or "μνήμη" in t:
        return {"type": "tool", "action": "memory"}

    if "ειδοποίηση" in t or "notification" in t:
        return {"type": "tool", "action": "notify"}

    if "internet" in t or "ίντερνετ" in t or "διαδίκτυο" in t:
        return {"type": "tool", "action": "internet"}

    
    if t.startswith("web ") or t.startswith("/web "):
        return {"type": "tool", "action": "web"}

    
    if t.startswith("cmd "):
        return {"type": "tool", "action": "cmd"}

    
    if t in ["sysinfo", "/sysinfo", "system info"]:
        return {"type": "tool", "action": "sysinfo"}

    
    if t in ["snapshot", "/snapshot", "project snapshot"]:
        return {"type": "tool", "action": "snapshot"}

    
    if t in ["compile", "/compile", "check code"]:
        return {"type": "tool", "action": "compile"}

    
    if t in ["memory summary", "σύνοψη μνήμης"]:
        return {"type": "tool", "action": "memory_summary"}

    
    if t.startswith("σχέδιο στόχου ") or t.startswith("plan goal "):
        return {"type": "tool", "action": "plan_goal"}

    if t.startswith("plan ") or t.startswith("σχέδιο "):
        return {"type": "tool", "action": "plan"}

    
    if t.startswith("task ") or t.startswith("εργασία "):
        return {"type": "tool", "action": "task"}

    if t in ["tasks", "εργασίες"]:
        return {"type": "tool", "action": "tasks"}

    
    if t.startswith("read source ") or t.startswith("/read-source "):
        return {"type": "tool", "action": "read_source"}

    
    if t in ["stable", "backup stable", "σταθερο"]:
        return {"type": "tool", "action": "stable"}

    
    if t.startswith("make plugin ") or t.startswith("φτιάξε plugin "):
        return {"type": "tool", "action": "make_plugin"}

    if t.startswith("run plugin ") or t.startswith("/plugin "):
        return {"type": "tool", "action": "run_plugin"}

    if t.startswith("test plugin "):
        return {"type": "tool", "action": "test_plugin"}

    if t.startswith("quarantine plugin "):
        return {"type": "tool", "action": "quarantine_plugin"}

    
    if t.startswith("σκέψου ") or t.startswith("think "):
        return {"type": "tool", "action": "think_deep"}

    if t.startswith("λύσε ") or t.startswith("solve "):
        return {"type": "tool", "action": "solve_problem"}

    if t.startswith("απόφαση ") or t.startswith("decide "):
        return {"type": "tool", "action": "decide"}

    
    if t.startswith("θυμήσου ") or t.startswith("remember "):
        return {"type": "tool", "action": "remember_fact"}

    if t.startswith("στόχος ") or t.startswith("goal "):
        return {"type": "tool", "action": "add_goal"}

    if t.startswith("project ") or t.startswith("έργο "):
        return {"type": "tool", "action": "add_project"}

    if t in ["profile", "state", "personal state", "κατάσταση νου"]:
        return {"type": "tool", "action": "personal_state"}

    if t.startswith("σχέδιο στόχου ") or t.startswith("plan goal "):
        return {"type": "tool", "action": "plan_goal"}

    
    if t in ["sense", "/sense", "αισθήσεις", "android sense"]:
        return {"type": "tool", "action": "sense"}

    
    if t in ["sense think", "σκέψου αισθήσεις", "ανάλυσε κινητό"]:
        return {"type": "tool", "action": "sense_think"}

    
    if t in ["git status", "git"]:
        return {"type": "tool", "action": "git_status"}

    if t.startswith("git checkpoint") or t.startswith("checkpoint"):
        return {"type": "tool", "action": "git_checkpoint"}

    if t in ["daily brief", "ημερήσια εικόνα"]:
        return {"type": "tool", "action": "daily_brief"}

    if t in ["battery guard", "έλεγχος μπαταρίας"]:
        return {"type": "tool", "action": "battery_guard"}

    if t.startswith("next action") or t.startswith("επόμενη ενέργεια"):
        return {"type": "tool", "action": "next_action"}

    if t in ["actions", "action log", "ιστορικό ενεργειών"]:
        return {"type": "tool", "action": "action_log"}

    
    if t.startswith("make app ") or t.startswith("φτιάξε app "):
        return {"type": "tool", "action": "make_app"}

    if t in ["cloud info", "cloud"]:
        return {"type": "tool", "action": "cloud_info"}

    
    if t.startswith("forge plugin ") or t.startswith("γράψε τέλειο plugin "):
        return {"type": "tool", "action": "forge_plugin"}

    
    if t in ["apps", "my apps", "εφαρμογές"]:
        return {"type": "tool", "action": "list_apps"}

    
    if t.startswith("search ") or t.startswith("ψάξε "):
        return {"type": "tool", "action": "web_search"}

    if t.startswith("open url ") or t.startswith("άνοιξε url "):
        return {"type": "tool", "action": "fetch_page"}

    if t.startswith("research ") or t.startswith("έρευνα "):
        return {"type": "tool", "action": "research"}

    
    if t.startswith("agent solve ") or t.startswith("λύσε στόχο "):
        return {"type": "tool", "action": "agent_solve"}

    if t.startswith("agent checkpoint ") or t.startswith("λύσε και σώσε "):
        return {"type": "tool", "action": "agent_checkpoint"}

    if t in ["agent review", "review agent", "έλεγχος agent"]:
        return {"type": "tool", "action": "agent_review"}

    
    if t.startswith("schedule ") or t.startswith("προγραμμάτισε "):
        return {"type": "tool", "action": "schedule_task"}

    if t in ["schedules", "scheduled tasks", "προγραμματισμένα"]:
        return {"type": "tool", "action": "list_schedules"}

    if t in ["clear schedules", "καθάρισε προγραμματισμένα"]:
        return {"type": "tool", "action": "clear_schedules"}

    
    if t.startswith("recall ") or t.startswith("θυμάσαι "):
        return {"type": "tool", "action": "recall"}

    if t in ["who am i", "τι ξέρεις για μένα", "τι θυμάσαι"]:
        return {"type": "tool", "action": "recall"}

    
    if t.startswith("team plan ") or t.startswith("ομάδα σχέδιο "):
        return {"type": "tool", "action": "team_plan"}

    if t.startswith("team solve ") or t.startswith("ομάδα λύσε "):
        return {"type": "tool", "action": "team_solve"}

    
    if t in ["repair system", "system repair", "επισκευή συστήματος"]:
        return {"type": "tool", "action": "repair_system"}

    if t in ["repair advice", "διάγνωση επισκευής"]:
        return {"type": "tool", "action": "repair_advice"}

    

    if t in ["autonomy start", "start autonomy", "ξεκίνα αυτονομία", "έναρξη αυτονομίας"]:
        return {"type": "tool", "action": "autonomy_start"}

    if t in ["autonomy stop", "stop autonomy", "σταμάτα αυτονομία", "παύση αυτονομίας"]:
        return {"type": "tool", "action": "autonomy_stop"}

    if t in ["autonomy status", "status autonomy", "κατάσταση αυτονομίας"]:
        return {"type": "tool", "action": "autonomy_status"}

    if t in ["autonomy", "autonomy cycle", "κύκλος αυτονομίας"]:
        return {"type": "tool", "action": "autonomy_cycle"}

    return {"type": "chat", "action": "chat"}











