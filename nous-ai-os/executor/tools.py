from executor.autonomy_v3 import autonomy_cycle
from executor import autonomy as autonomy_state
from executor.repair_agent import repair_check, repair_advice
from executor.team_agent import team_plan, team_solve
from executor.long_memory import recall
from executor.scheduler_agent import add_schedule, list_schedules, clear_schedules
from executor.agent_executor import solve_goal, solve_and_checkpoint
from executor.agent_review import review_last
from executor.research_agent import web_search, fetch_page, research
from executor.code_forge import forge_plugin
from executor.app_builder import make_web_app, list_apps
from executor.git_agent import git_status, git_checkpoint
from executor.daily_brief import daily_brief
from executor.battery_guard import battery_guard
from executor.project_agent import next_action
from executor.action_log import log_action, recent_actions
from executor.sense_brain import sense_and_think
from executor.android_sense import sense
from executor.personal_agent import remember_fact, add_goal, add_project, list_state, plan_goal
from executor.thinking_tools import think_deep, solve_problem, decide
from executor.plugin_ai import generate_plugin
from executor.plugin_tester import test_plugin
from executor.plugin_quarantine import quarantine
from executor.plugin_registry import run_plugin
from executor.plugin_registry import list_plugins
from executor.memory import load
from executor.notifications import notify
from executor.web_agent import web_command
from executor.command_tools import run_command
from executor.system_info import info as system_info
from executor.project_snapshot import snapshot as project_snapshot
from executor.compile_check import check as compile_check
from executor.memory_tools import recent as memory_recent, summary as memory_summary
from executor.planner import make_plan
from executor.task_state import add_task, list_tasks
from executor.source_reader import read_source
from executor.stability import stable_point

def run_tool(intent, context=None):

    action = intent.get("action")

    if action == "plugin":
        return "Plugins: " + ", ".join(list_plugins())

    if action == "memory":
        return load()[-20:]

    if action == "notify":
        notify("ΝΟΥΣ AI", "Ο ΝΟΥΣ είναι ενεργός")
        return "notification_sent"

    if action == "internet":
        return "Internet gateway module installed"

    
    if action == "web":
        return web_command(context.get("command", "") if isinstance(context, dict) else "")

    
    if action == "cmd":
        c = context.get("command", "").replace("cmd ", "", 1)
        return run_command(c)

    
    if action == "sysinfo":
        return system_info()

    
    if action == "snapshot":
        return project_snapshot()

    
    if action == "compile":
        return compile_check()

    
    if action == "memory_summary":
        return memory_summary()

    
    if action == "plan":
        return make_plan(context.get("command", ""))

    
    if action == "task":
        return add_task(context.get("command", ""))

    if action == "tasks":
        return list_tasks()

    
    if action == "read_source":
        cmd = context.get("command", "")
        path = cmd.replace("read source ", "").replace("/read-source ", "").strip()
        return read_source(path)

    
    if action == "stable":
        return stable_point()

    
    if action == "make_plugin":
        goal = context.get("command", "").replace("make plugin ", "").replace("φτιάξε plugin ", "").strip()
        return generate_plugin(goal)

    if action == "run_plugin":
        name = context.get("command", "").replace("run plugin ", "").replace("/plugin ", "").strip()
        return run_plugin(name)

    if action == "test_plugin":
        name = context.get("command", "").replace("test plugin ", "").strip()
        return test_plugin(name)

    if action == "quarantine_plugin":
        name = context.get("command", "").replace("quarantine plugin ", "").strip()
        return quarantine(name)

    
    if action == "think_deep":
        return think_deep(context.get("command", ""))

    if action == "solve_problem":
        return solve_problem(context.get("command", ""))

    if action == "decide":
        return decide(context.get("command", ""))

    
    if action == "remember_fact":
        text = context.get("command", "").replace("θυμήσου ", "").replace("remember ", "").strip()
        return remember_fact(text)

    if action == "add_goal":
        text = context.get("command", "").replace("στόχος ", "").replace("goal ", "").strip()
        return add_goal(text)

    if action == "add_project":
        text = context.get("command", "").replace("project ", "").replace("έργο ", "").strip()
        return add_project(text)

    if action == "personal_state":
        return list_state()

    if action == "plan_goal":
        text = context.get("command", "").replace("σχέδιο στόχου ", "").replace("plan goal ", "").strip()
        return plan_goal(text)

    
    if action == "sense":
        return sense()

    
    if action == "sense_think":
        return sense_and_think()

    
    if action == "git_status":
        return git_status()

    if action == "git_checkpoint":
        msg = context.get("command", "").replace("git checkpoint", "").replace("checkpoint", "").strip() or "NOUS auto checkpoint"
        return git_checkpoint(msg)

    if action == "daily_brief":
        return daily_brief()

    if action == "battery_guard":
        return battery_guard()

    if action == "next_action":
        return next_action(context.get("command", ""))

    if action == "action_log":
        return recent_actions()

    
    if action == "make_app":
        name = context.get("command", "").replace("make app ", "").replace("φτιάξε app ", "").strip() or "nous_app"
        return make_web_app(name, title=name, body="Web app generated by ΝΟΥΣ AI OS")

    if action == "cloud_info":
        return {
            "ready": True,
            "files": ["requirements.txt", "Procfile", "Dockerfile", "runtime.txt"],
            "run": "python -m executor.router"
        }


    
    if action == "forge_plugin":
        goal = context.get("command", "").replace("forge plugin ", "").replace("γράψε τέλειο plugin ", "").strip()
        return forge_plugin(goal)


    
    if action == "list_apps":
        return list_apps()

    
    if action == "web_search":
        q = context.get("command", "").replace("search ", "").replace("ψάξε ", "").strip()
        return web_search(q)

    if action == "fetch_page":
        url = context.get("command", "").replace("open url ", "").replace("άνοιξε url ", "").strip()
        return fetch_page(url)

    if action == "research":
        q = context.get("command", "").replace("research ", "").replace("έρευνα ", "").strip()
        return research(q)


    
    if action == "agent_solve":
        goal = context.get("command", "").replace("agent solve ", "").replace("λύσε στόχο ", "").strip()
        return solve_goal(goal)

    if action == "agent_checkpoint":
        goal = context.get("command", "").replace("agent checkpoint ", "").replace("λύσε και σώσε ", "").strip()
        return solve_and_checkpoint(goal)

    if action == "agent_review":
        return review_last()


    
    if action == "schedule_task":
        text = context.get("command", "").replace("schedule ", "").replace("προγραμμάτισε ", "").strip()
        return add_schedule(text)

    if action == "list_schedules":
        return list_schedules()

    if action == "clear_schedules":
        return clear_schedules()


    
    if action == "recall":
        q = context.get("command", "").replace("recall ", "").replace("θυμάσαι ", "").strip()
        return recall(q)


    
    if action == "team_plan":
        goal = context.get("command", "").replace("team plan ", "").replace("ομάδα σχέδιο ", "").strip()
        return team_plan(goal)

    if action == "team_solve":
        goal = context.get("command", "").replace("team solve ", "").replace("ομάδα λύσε ", "").strip()
        return team_solve(goal)


    
    if action == "repair_system":
        return repair_check()

    if action == "repair_advice":
        return repair_advice()


    

    if action == "autonomy_start":
        return autonomy_state.start()

    if action == "autonomy_stop":
        return autonomy_state.stop()

    if action == "autonomy_status":
        return autonomy_state.status()


    if action == "autonomy_cycle":
        return autonomy_cycle()


    return "UNKNOWN TOOL"











