from pathlib import Path
import os
import sys
import platform
import time
from flask import Flask, request, jsonify, send_from_directory
from executor.document_chat_bridge import document_chat_answer, format_document_answer
from executor.chat_response_engine import chatgpt_style_response
from executor.upload_processing_engine import process_uploaded_file, upload_status
from executor.conversation_manager import list_conversations, get_conversation, rename_conversation, delete_conversation
from executor.conversation_search_engine import search_conversations
from executor.conversation_title_engine import generate_conversation_title, auto_title_recent_conversations
from executor.knowledge_memory_engine import status as knowledge_memory_status, search_knowledge, remember_knowledge, search_code_lessons
from executor.patch_quality_gate import quality_gate
from executor.error_learning_engine import status as error_learning_status, search_errors, search_solutions
from executor.field_engine import add_entry, list_entries, delete_entry, get_map_markers
from executor.remote_llm import ask_with_image
from executor.nous_ui import nous_dashboard_html
from executor.kernel import handle
from executor.control_center import CONTROL_CENTER_HTML
from executor.security import check_token, check_admin_token
from executor.auth_guard import install_auth_guard
from executor.api_tokens import create_token, list_tokens, revoke_token, token_stats
from executor import autonomy as autonomy_state
from executor.autonomy_service import enable as service_enable, disable as service_disable, status as service_status, run_cycle as service_run_cycle, watchdog_check
from executor.goal_executor import goal_executor_cycle
from executor.project_progress import list_progress, project_summary, sync_projects, mark_step
from executor.self_healing_runtime import self_heal_check
from executor.task_queue import list_queue, clear_queue, retry_failed, recover_dead_tasks
from executor.runtime_metrics import collect_metrics
from executor.curiosity_agent import curiosity_cycle, knowledge_status, load_queue, load_knowledge, add_topic, mark_learned, active_learning_topics
from executor.learning_engine import learning_status, learning_run
from executor.android_control import android_status, android_notify, android_safe_commands, android_open_url
from executor.app_evolver import app_evolution_status, queue_app_improvement
from executor.local_llm_adapter import local_llm_status, ask_local
from executor.decision_engine import decide_next_action, prioritize_goals
from executor.real_action_executor import agent_act_cycle
from executor.guardian_policy import check_action, policy_status
from executor.real_research_engine import research_to_knowledge, research_status, learned_items
from executor.master_agent import master_state, choose_master_priority, master_cycle
from executor.self_improvement_engine import self_improvement_status, create_patch_request, list_patches, apply_patch
from executor.internet_learning_pipeline import internet_learning_status, internet_learn_topic, internet_learn_url
from executor.complex_action_runner import complex_action_status, run_complex_action
from executor.deploy_operator import deploy_operator_status, prepare_real_deploy
from executor.reality_gate import reality_status
from executor.real_action_chains import real_chain_status, run_real_chain
from executor.deploy_provider_manager import deploy_provider_status, deploy_with_provider
from executor.vercel_deploy_integration import vercel_status, vercel_deploy
from executor.remote_browser_bridge import remote_browser_bridge_status, create_browser_job, list_browser_jobs, complete_browser_job
from executor.operator_backend_router import operator_backend_status, browser_backend_status, android_backend_status, deployment_backend_status
from executor.device_control_backend import device_control_status, device_control_recommendation
from executor.companion_bridge import companion_status, companion_home, companion_back, companion_ui_tree, companion_tap, companion_logs, companion_ui_tree_with_logs
from executor.ops_console import ops_status, run_ops_action
from executor.mission_system import mission_status, list_missions, create_mission, create_standard_mission, run_next_mission_task, run_mission_cycle, approve_task, pending_approvals
from executor.autonomous_workspace import workspace_status, plan_from_prompt, create_workspace_mission, run_workspace_mission
from executor.executive_layer import executive_status, executive_plan, executive_run
from executor.goal_system import goal_status, list_goals, create_goal, seed_core_goals, add_goal_note, link_mission_to_goal, refresh_goal_progress, create_goal_mission
from executor.brain_state import brain_status, build_brain_state, save_brain_state, load_brain_state
from executor.cloud_brain_backup import brain_backup_status, create_brain_backup, list_brain_backups
from executor.brain_restore import restore_status, inspect_brain_backup, restore_brain_backup
from executor.decision_memory import decision_status, list_decisions, search_decisions, record_decision
from executor.learning_memory import lesson_status, list_lessons, search_lessons, record_lesson
from executor.executive_intelligence import executive_intelligence_status, executive_intelligence_report
from executor.recommendation_actions import execute_recommendation, reject_recommendation
from executor.executive_scheduler import executive_scheduler_status, run_executive_review, list_executive_reviews
from executor.executive_scheduler_loop import scheduler_loop_status, start_scheduler_loop, stop_scheduler_loop, run_scheduler_once, reconcile_scheduler_loop_state
from executor.goal_progress_intelligence import goal_progress_intelligence_status, analyze_goal_progress, apply_goal_progress_intelligence
from executor.mission_planner import mission_planner_status, list_mission_proposals, propose_mission_for_goal, approve_mission_proposal, reject_mission_proposal
from executor.dashboard_action_audit import dashboard_action_audit
from executor.self_diagnosis import self_diagnosis_status, run_self_diagnosis, apply_safe_self_fix
from executor.autonomous_repair import repair_status, list_repair_proposals, propose_repair_from_diagnosis, approve_repair_proposal, reject_repair_proposal
from executor.auto_mission_executor import auto_mission_executor_status, run_auto_mission_executor, set_auto_mission_executor_enabled
from executor.code_analyst import code_analyst_status, list_code_analysis_reports, analyze_problem, analyze_latest_diagnosis, generate_patch_suggestion
from executor.auto_mission_scheduler import auto_mission_scheduler_status, start_auto_mission_scheduler, stop_auto_mission_scheduler, run_auto_mission_scheduler_once, reconcile_auto_mission_scheduler
from executor.executive_loop_v2 import executive_loop_v2_status, run_executive_loop_v2
from executor.pending_review import pending_review_status
from executor.executive_command_center import executive_command_center_status, run_executive_command_cycle
from executor.deep_code_analyst import deep_code_analyst_status, list_deep_code_reports, analyze_failure, analyze_latest_diagnosis_deep
from executor.self_healing_loop import self_healing_status, run_self_healing_analysis
from executor.patch_generator import patch_generator_status, list_patch_proposals, approve_patch_proposal, reject_patch_proposal
from executor.cleanup_engine import cleanup_status, list_cleanup_reports, run_cleanup_preview, apply_cleanup
from executor.goal_manager_v2 import goal_manager_status, generate_projects_from_goals, update_project_progress, list_goal_projects
from executor.executive_memory_v3 import executive_memory_status, search_executive_memory, learn_from_recent_state
from executor.upgrade_planner import upgrade_planner_status, list_upgrade_plans, propose_upgrade_plan, approve_upgrade_plan, reject_upgrade_plan, get_plan as upgrade_get_plan
from executor.nous_drive import (
    think as nous_drive_think, status as nous_drive_status,
    list_pending as nous_drive_pending, list_proposals as nous_drive_proposals,
    approve_proposal as nous_drive_approve, reject_proposal as nous_drive_reject,
    get_proposal as nous_drive_get_proposal,
)
from executor.weather_engine import get_weather, weather_status
from executor.gps_tracker import update_position as gps_update_pos, gps_status, get_track as gps_get_track, clear_track as gps_clear_track
from executor.voice_engine import voice_status, prepare_tts
from executor.web_search import search as web_search_fn
from executor.scheduler_cron import cron_status, list_jobs as cron_list_jobs, add_job as cron_add_job, remove_job as cron_remove_job, toggle_job as cron_toggle_job, start_scheduler
from executor.patch_apply_engine import patch_apply_status, list_patch_apply_history, apply_patch_proposal
from executor.rollback_engine import rollback_status, list_rollbacks, rollback_backup
from executor.repository_graph import repository_graph_status, build_repository_graph
from executor.knowledge_graph import knowledge_graph_status, build_knowledge_graph
from executor.executive_loop_v3 import executive_loop_v3_status, run_executive_loop_v3
from executor.browser_driver_operator import browser_driver_status, run_browser_actions
from executor.operator_capability_manager import operator_capabilities as operator_capability_status, reality_flags
from executor.real_action_gate import real_actions_status, run_real_action, available_real_actions
from executor.android_operator import android_operator_status, tap as android_tap, swipe as android_swipe, keyevent as android_keyevent
from executor.browser_operator import browser_operator_status, open_url as operator_open_url, prepare_click, prepare_fill_form, prepare_login
from executor.operator_approval import list_approvals, approve, reject
from executor.git_workflow import git_workflow_status, git_safe_checkpoint
from executor.web_deploy_manager import deploy_status, register_local_deploy, deploy_git_status
from executor.android_actions_v2 import android_actions_status, run_android_action
from executor.browser_automation import browser_status, browser_search, browser_read
from executor.multi_agent_team import team_status, team_cycle
from executor.agent_journal import list_journal
from executor.progress_linker import progress_snapshot, link_task_to_project
from executor.goal_progress import list_goal_progress, refresh_goal_progress, goal_progress_summary
from executor.app_factory_v2 import create_app_from_idea, queue_app_idea, app_factory_status
from executor.code_assistant import code_health, code_advice
from executor.research_browser_agent import research_query, read_url
from executor.knowledge_research import research_next_topic, learning_cycle

# Φόρτωση .env (κλειδιά εκτός κώδικα) — προαιρετικό dependency
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

app = Flask(__name__)

# Fail-closed auth για ΟΛΑ τα endpoints (δες executor/auth_guard.py)
install_auth_guard(app)

try:
    reconcile_scheduler_loop_state()
    reconcile_auto_mission_scheduler()
except Exception:
    pass

@app.route("/")
def home():
    return nous_dashboard_html()

def _chat_intent_route(msg: str):
    """Detect app-build / upgrade intents in chat and route them automatically.
    Returns a response dict if intent matched, None otherwise.
    """
    import threading as _th
    import re as _re

    if not msg or len(msg.strip()) < 4:
        return None

    m = msg.lower().strip()

    # ── Detect: "φτιάξε / δημιούργησε / φτιάξε μου / κάνε / make / build / create" + app/εφαρμογή
    _APP_VERBS = r"(φτιάξε|φτιάξε μου|δημιούργησε|κάνε|φτιαχτεί|make|build|create|σχεδίασε)"
    _APP_NOUNS = r"(app|εφαρμογή|application|webapp|web app|πρόγραμμα|tool|εργαλείο)"
    if _re.search(_APP_VERBS, m) and _re.search(_APP_NOUNS, m):
        def _build():
            try:
                result = plan_app(msg)
                plan_id = result.get("plan_id")
                if plan_id and result.get("ok") is not False:
                    approve_and_write(plan_id)
            except Exception:
                pass
        _th.Thread(target=_build, daemon=True).start()
        app_hint = msg[:80].strip()
        return {
            "ok": True,
            "source": "chat_intent_app_builder",
            "answer": (
                f"🚀 **Ξεκίνησε η κατασκευή!**\n\n"
                f"Ο ΝΟΥΣ δουλεύει στην εφαρμογή: *{app_hint}*\n\n"
                f"➡️ Πήγαινε στο **App Builder** → tab «Builds» για να δεις την πρόοδο και να την τρέξεις όταν είναι έτοιμη.\n\n"
                f"⏱️ Συνήθως χρειάζεται 10–30 δευτερόλεπτα."
            ),
            "response": "App build ξεκίνησε — δες App Builder → Builds.",
            "text": "App build ξεκίνησε — δες App Builder → Builds.",
            "executed": True,
            "intent": "build_app",
            "nav_hint": "app_builder",
        }

    # ── Detect: "αναβάθμισε / upgrade / βελτίωσε + τον εαυτό / τον ΝΟΥΣ / σου"
    _UPG_VERBS = r"(αναβάθμισε|αναβάθμιση|upgrade|βελτίωσε|βελτίωση|improve|update)"
    _UPG_TARGET = r"(εαυτό|νους|nous|σου|σε|yourself|yourself)"
    if _re.search(_UPG_VERBS, m) and (_re.search(_UPG_TARGET, m) or "αναβάθμιση" in m or "upgrade" in m):
        def _upgrade():
            try:
                result = propose_upgrade_plan()
                plan_id = str(result.get("plan", {}).get("id", ""))
                if plan_id and not result.get("deduped"):
                    approve_upgrade_plan(plan_id)
            except Exception:
                pass
        _th.Thread(target=_upgrade, daemon=True).start()
        return {
            "ok": True,
            "source": "chat_intent_upgrade",
            "answer": (
                "🔧 **Ξεκίνησε η αναβάθμιση NOUS!**\n\n"
                "Ο ΝΟΥΣ αναλύει και γράφει τον νέο κώδικα αυτόματα.\n\n"
                "➡️ Πήγαινε στο **App Builder** → «Πρωτοβουλίες» για να παρακολουθείς την εκτέλεση.\n\n"
                "⏱️ Διαρκεί 30–60 δευτερόλεπτα."
            ),
            "response": "Upgrade NOUS ξεκίνησε.",
            "text": "Upgrade NOUS ξεκίνησε.",
            "executed": True,
            "intent": "upgrade_nous",
            "nav_hint": "initiatives",
        }

    return None  # no intent matched — fall through to normal chat


@app.route("/chat", methods=["POST"])
def chat():

    # ── INTENT ROUTING (πριν από όλα τα early returns) ───────────────────────
    try:
        _raw = request.get_json(silent=True) or {}
        _intent_msg = (
            _raw.get("message") or _raw.get("prompt")
            or _raw.get("text") or _raw.get("command") or ""
        )
        _routed = _chat_intent_route(str(_intent_msg))
        if _routed is not None:
            return jsonify(_routed)
    except Exception:
        pass

    # NOUS_CHATGPT_STYLE_EARLY_RETURN
    try:
        data = request.get_json(silent=True) or {}
        msg = (
            data.get("message")
            or data.get("prompt")
            or data.get("text")
            or data.get("command")
            or ""
        )
        clean_chat = chatgpt_style_response(str(msg))
        if clean_chat is not None:
            return jsonify(clean_chat)
    except Exception:
        pass




    # NOUS_DOCUMENT_CHAT_EARLY_RETURN
    try:
        data = request.get_json(silent=True) or {}
        msg = (
            data.get("message")
            or data.get("prompt")
            or data.get("text")
            or data.get("command")
            or ""
        )
        doc_result = document_chat_answer(str(msg))
        doc_answer = format_document_answer(str(msg))
        if doc_result.get("used_documents") and doc_result.get("sources"):
            return jsonify({
                "ok": True,
                "executed": False,
                "source": "document_chat_bridge",
                "mode": "document_recall",
                "human_answer": doc_answer,
                "answer": doc_answer,
                "response": doc_answer,
                "text": doc_answer,
                "summary": "Απάντηση από μαθημένο έγγραφο.",
                "sources": doc_result.get("sources", []),
                "raw": doc_result
            })
    except Exception:
        pass

    try:
        data = request.get_json(silent=True) or {}
        msg = (
            data.get("message")
            or data.get("prompt")
            or data.get("text")
            or data.get("command")
            or ""
        )
        doc_answer = format_document_answer(str(msg))
        if doc_answer:
            return jsonify({
                "ok": True,
                "source": "document_chat_bridge",
                "mode": "document_recall",
                "answer": doc_answer,
                "response": doc_answer,
                "text": doc_answer
            })
    except Exception as e:
        pass

    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json()
    cmd = data.get("command", "")

    # ── CHAT INTENT ROUTING ───────────────────────────────────────────────────
    try:
        _routed = _chat_intent_route(cmd)
        if _routed is not None:
            return jsonify(_routed)
    except Exception:
        pass

    return jsonify(handle(cmd, {}))

from executor.health import backup as create_backup
from executor.health import status as health_status

from executor.remote_tunnel import start_tunnel, stop_tunnel, tunnel_status as get_tunnel_status
from executor.larmor_bridge import (
    ping_larmor_app, calculate_larmor, analyze_session, larmor_chat,
    MATERIALS, METAL_EM_PROPERTIES, get_knowledge_chunks, optimal_em_frequency_hz,
    characteristic_frequency_hz, SOIL_TYPES, AGE_FACTORS,
)

@app.route("/larmor/ping")
def larmor_ping():
    return jsonify(ping_larmor_app())

@app.route("/larmor/materials")
def larmor_materials():
    return jsonify(MATERIALS)

@app.route("/larmor/calculate", methods=["POST"])
def larmor_calculate():
    data = request.get_json(silent=True) or {}
    material = data.get("material", "cu")
    b_field = float(data.get("b_field_T", 0.048))
    return jsonify(calculate_larmor(material, b_field))

@app.route("/larmor/analyze", methods=["POST"])
def larmor_analyze():
    data = request.get_json(silent=True) or {}
    session_data = data.get("session_data", "")
    question = data.get("question", "")
    if not session_data:
        return jsonify({"error": "Δεν δόθηκαν δεδομένα για ανάλυση"}), 400
    result = analyze_session(session_data, question)
    return jsonify({"analysis": result})

@app.route("/larmor/chat", methods=["POST"])
def larmor_chat_route():
    data = request.get_json(silent=True) or {}
    conversation = data.get("conversation", [])
    if not conversation:
        return jsonify({"error": "Χωρίς μήνυμα"}), 400
    reply = larmor_chat(conversation)
    return jsonify({"reply": reply})

@app.route("/larmor/em-calculator", methods=["POST"])
def larmor_em_calculator():
    """Calculate optimal EM frequency for a buried metallic object (classical Faraday/eddy-current model)."""
    data = request.get_json(silent=True) or {}
    metal_key   = data.get("metal", "22k_alloy")
    radius_cm   = float(data.get("radius_cm", 3.0))
    depth_m     = float(data.get("depth_m", 1.5))
    soil_key    = data.get("soil", "medium")
    age_key     = data.get("age", "guerrilla")

    soil  = SOIL_TYPES.get(soil_key, SOIL_TYPES["medium"])
    age   = AGE_FACTORS.get(age_key, AGE_FACTORS["guerrilla"])

    result = optimal_em_frequency_hz(
        metal_key  = metal_key,
        radius_m   = radius_cm / 100.0,
        depth_m    = depth_m,
        soil_sigma = soil["sigma"],
        age_factor = age["factor"],
    )
    if "error" in result:
        return jsonify(result), 400

    # Also supply f_char table for a range of radii
    metal = METAL_EM_PROPERTIES.get(metal_key, {})
    sigma = metal.get("sigma", 1e7)
    mu_r  = metal.get("mu_r", 1.0)
    size_table = []
    for r_cm in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0, 15.0, 20.0]:
        fc = characteristic_frequency_hz(sigma, mu_r, r_cm / 100.0)
        size_table.append({"radius_cm": r_cm, "f_char_hz": round(fc, 1)})

    result["size_table"] = size_table
    result["soil_name"]  = soil["name"]
    result["age_desc"]   = age["desc"]
    return jsonify(result)

@app.route("/larmor/inject-knowledge", methods=["POST"])
def larmor_inject_knowledge():
    """Inject all Larmor/NMR domain knowledge into the NOUS brain."""
    from executor.knowledge_memory_engine import remember_knowledge
    chunks = get_knowledge_chunks()
    stored, skipped = 0, 0
    for chunk in chunks:
        result = remember_knowledge(
            question=chunk["question"],
            answer=chunk["answer"],
            sources=[{"document": "larmor_domain_knowledge"}],
            kind="research",
            confidence="high",
            tags=chunk.get("tags", ["larmor", "NMR"]),
        )
        if result.get("stored"):
            stored += 1
        else:
            skipped += 1
    return jsonify({"ok": True, "stored": stored, "skipped": skipped, "total": len(chunks)})

@app.route("/larmor/inject-guerrilla-knowledge", methods=["POST"])
def inject_guerrilla_knowledge():
    """Inject guerrilla signs, military maps & Byzantine/Ottoman symbols knowledge into NOUS."""
    from executor.knowledge_memory_engine import remember_knowledge
    from executor.guerrilla_signs_knowledge import get_guerrilla_signs_chunks
    chunks = get_guerrilla_signs_chunks()
    stored, skipped = 0, 0
    for chunk in chunks:
        result = remember_knowledge(
            question=chunk["question"],
            answer=chunk["answer"],
            sources=[{"document": "Guerrilla_Signs_MilitaryMaps_ByzOttoman"}],
            kind="research",
            confidence="high",
            tags=chunk.get("tags", ["αντάρτες", "χάρτες", "WWII"]),
        )
        if result.get("stored"):
            stored += 1
        else:
            skipped += 1
    return jsonify({
        "ok": True,
        "stored": stored,
        "skipped": skipped,
        "total": len(chunks),
        "source": "Αντάρτικα Σημάδια / Στρατ. Χάρτες / Βυζ-Οθωμ. Σύμβολα",
    })

@app.route("/larmor/inject-cache-knowledge", methods=["POST"])
def inject_cache_knowledge():
    """Inject US Army SF Caching Techniques (ST 31-205) knowledge into NOUS brain."""
    from executor.knowledge_memory_engine import remember_knowledge
    from executor.cache_knowledge import get_cache_knowledge_chunks
    chunks = get_cache_knowledge_chunks()
    stored, skipped = 0, 0
    for chunk in chunks:
        result = remember_knowledge(
            question=chunk["question"],
            answer=chunk["answer"],
            sources=[{"document": "SF_Caching_Techniques_ST31-205"}],
            kind="research",
            confidence="high",
            tags=chunk.get("tags", ["cache", "WWII", "αντάρτες"]),
        )
        if result.get("stored"):
            stored += 1
        else:
            skipped += 1
    return jsonify({
        "ok": True,
        "stored": stored,
        "skipped": skipped,
        "total": len(chunks),
        "source": "US Army SF Caching Techniques ST 31-205",
    })

@app.route("/health")
def health():
    return jsonify(health_status())

@app.route("/remote/tunnel/status")
def tunnel_status_route():
    return jsonify(get_tunnel_status())

@app.route("/remote/tunnel/start", methods=["POST"])
def tunnel_start_route():
    data = request.get_json(silent=True) or {}
    authtoken = data.get("authtoken", "").strip() or None
    result = start_tunnel(port=5000, authtoken=authtoken)
    return jsonify(result)

@app.route("/remote/tunnel/stop", methods=["POST"])
def tunnel_stop_route():
    return jsonify(stop_tunnel())

@app.route("/remote/tunnel/save-token", methods=["POST"])
def tunnel_save_token_route():
    data = request.get_json(silent=True) or {}
    token = data.get("authtoken", "").strip()
    if not token:
        return jsonify({"ok": False, "error": "Κενό token"})
    try:
        env_path = ".env"
        lines = []
        found = False
        if os.path.exists(env_path):
            with open(env_path) as f:
                lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.startswith("NGROK_AUTHTOKEN="):
                new_lines.append(f"NGROK_AUTHTOKEN={token}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"NGROK_AUTHTOKEN={token}\n")
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        os.environ["NGROK_AUTHTOKEN"] = token
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/system-info")
def system_info():
    try:
        import psutil, time
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot = psutil.boot_time()
        uptime_sec = int(time.time() - boot)
        uptime_h = uptime_sec // 3600
        uptime_m = (uptime_sec % 3600) // 60

        # NOUS process RAM
        import os
        try:
            proc = psutil.Process(os.getpid())
            nous_ram_mb = round(proc.memory_info().rss / 1024 / 1024, 1)
        except Exception:
            nous_ram_mb = None

        return jsonify({
            "cpu_percent": cpu,
            "ram_used_gb": round(mem.used / 1024**3, 2),
            "ram_total_gb": round(mem.total / 1024**3, 2),
            "ram_percent": mem.percent,
            "disk_used_gb": round(disk.used / 1024**3, 1),
            "disk_total_gb": round(disk.total / 1024**3, 1),
            "disk_percent": disk.percent,
            "uptime": f"{uptime_h}ω {uptime_m}λ",
            "nous_ram_mb": nous_ram_mb,
            "platform": platform.system(),
        })
    except ImportError:
        return jsonify({"error": "psutil not installed", "hint": "pip install psutil"})
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route("/token/create", methods=["POST"])
def token_create_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    name = data.get("name", "remote")
    return jsonify(create_token(name))


@app.route("/token/list")
def token_list_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(list_tokens())


@app.route("/token/revoke", methods=["POST"])
def token_revoke_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    token_id = data.get("id")
    return jsonify(revoke_token(token_id))

@app.route("/runtime")
def runtime_route():
    return jsonify({
        "system": "NOUS AI OS",
        "level": 22,
        "python": sys.version,
        "platform": platform.platform(),
        "time": time.time(),
        "cloud_ready": True,
        "host": "0.0.0.0",
        "port": int(os.environ.get("PORT", "5000")),
    })


@app.route("/cloud/status")
def cloud_status_route():
    return jsonify({
        "cloud_ready": True,
        "runtime_endpoint": "/runtime",
        "health_endpoint": "/health",
        "chat_endpoint": "/chat",
        "apps_endpoint": "/apps",
        "port_env": os.environ.get("PORT"),
        "default_port": 5000,
        "tokens": token_stats(),
    })

@app.route("/backup")
def backup_route():
    return jsonify(create_backup())

from executor.file_reader import save_upload, read_text

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no_file"})
    return jsonify(save_upload(f))

@app.route("/read-file", methods=["POST"])
def read_file_route():
    data = request.get_json()
    path = data.get("path", "")
    return jsonify({"content": read_text(path)})


from executor.image_reader import save_image, image_preview

@app.route("/upload-image", methods=["POST"])
def upload_image():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no_image"})
    return jsonify(save_image(f))

@app.route("/image-preview", methods=["POST"])
def image_preview_route():
    data = request.get_json()
    path = data.get("path", "")
    return jsonify(image_preview(path))


from executor.android_sense import sense as android_sense

@app.route("/sense")
def sense_route():
    return jsonify(android_sense())


from executor.app_builder import list_apps, plan_app, approve_and_write, reject_plan, list_builds, get_build, status as app_builder_status










@app.route("/remote/research/query", methods=["POST"])
def remote_research_query_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(research_query(
        data.get("query", ""),
        bool(data.get("learn", False)),
        data.get("topic")
    ))


@app.route("/remote/browser/read", methods=["POST"])
def remote_browser_read_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(read_url(
        data.get("url", ""),
        bool(data.get("learn", False)),
        data.get("topic")
    ))






@app.route("/remote/goals/progress")
def remote_goals_progress_route():
    return jsonify(list_goal_progress())


@app.route("/remote/goals/refresh", methods=["POST"])
def remote_goals_refresh_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(refresh_goal_progress())


@app.route("/remote/goals/summary")
def remote_goals_summary_route():
    return jsonify(goal_progress_summary())

@app.route("/remote/progress/snapshot")
def remote_progress_snapshot_route():
    return jsonify(progress_snapshot())


@app.route("/remote/progress/link-task", methods=["POST"])
def remote_progress_link_task_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(link_task_to_project(data))













@app.route("/remote/companion/logs")
def remote_companion_logs_route():
    return jsonify(companion_logs())


@app.route("/remote/companion/ui-tree-logs", methods=["POST"])
def remote_companion_ui_tree_logs_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(companion_ui_tree_with_logs())



























@app.route("/remote/patch-apply/status")
def remote_patch_apply_status():
    return jsonify(patch_apply_status())

@app.route("/remote/patch-apply/history")
def remote_patch_apply_history():
    return jsonify(list_patch_apply_history())

@app.route("/remote/patch-apply/apply", methods=["POST"])
def remote_patch_apply_apply():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(apply_patch_proposal(data.get("proposal_id")))

@app.route("/remote/rollback/status")
def remote_rollback_status():
    return jsonify(rollback_status())

@app.route("/remote/rollback/history")
def remote_rollback_history():
    return jsonify(list_rollbacks())

@app.route("/remote/rollback/apply", methods=["POST"])
def remote_rollback_apply():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(rollback_backup(data.get("backup_id")))

@app.route("/remote/repository-graph/status")
def remote_repository_graph_status():
    return jsonify(repository_graph_status())

@app.route("/remote/repository-graph/build", methods=["POST"])
def remote_repository_graph_build():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(build_repository_graph())

@app.route("/remote/knowledge-graph/status")
def remote_knowledge_graph_status():
    return jsonify(knowledge_graph_status())

@app.route("/remote/knowledge-graph/build", methods=["POST"])
def remote_knowledge_graph_build():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(build_knowledge_graph())

@app.route("/remote/executive-loop-v3/status")
def remote_executive_loop_v3_status():
    return jsonify(executive_loop_v3_status())

@app.route("/remote/executive-loop-v3/run", methods=["POST"])
def remote_executive_loop_v3_run():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_executive_loop_v3(data.get("trigger", "dashboard")))

@app.route("/remote/cleanup/status")
def remote_cleanup_status():
    return jsonify(cleanup_status())


@app.route("/remote/cleanup/reports")
def remote_cleanup_reports():
    return jsonify(list_cleanup_reports())


@app.route("/remote/cleanup/preview", methods=["POST"])
def remote_cleanup_preview():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(run_cleanup_preview())


@app.route("/remote/cleanup/apply", methods=["POST"])
def remote_cleanup_apply():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(apply_cleanup())


@app.route("/remote/goal-manager-v2/status")
def remote_goal_manager_v2_status():
    return jsonify(goal_manager_status())


@app.route("/remote/goal-manager-v2/projects")
def remote_goal_manager_v2_projects():
    return jsonify(list_goal_projects())


@app.route("/remote/goal-manager-v2/generate", methods=["POST"])
def remote_goal_manager_v2_generate():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(generate_projects_from_goals())


@app.route("/remote/goal-manager-v2/update-progress", methods=["POST"])
def remote_goal_manager_v2_update():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(update_project_progress())


@app.route("/remote/executive-memory-v3/status")
def remote_executive_memory_v3_status():
    return jsonify(executive_memory_status())


@app.route("/remote/executive-memory-v3/search", methods=["POST"])
def remote_executive_memory_v3_search():
    data = request.get_json(silent=True) or {}
    return jsonify(search_executive_memory(data.get("query", "")))


@app.route("/remote/executive-memory-v3/learn", methods=["POST"])
def remote_executive_memory_v3_learn():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(learn_from_recent_state())


@app.route("/remote/upgrade-planner/status")
def remote_upgrade_planner_status():
    return jsonify(upgrade_planner_status())


@app.route("/remote/upgrade-planner/plans")
def remote_upgrade_planner_plans():
    return jsonify(list_upgrade_plans())


@app.route("/remote/upgrade-planner/propose", methods=["POST"])
def remote_upgrade_planner_propose():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(propose_upgrade_plan())


@app.route("/remote/upgrade-planner/approve", methods=["POST"])
def remote_upgrade_planner_approve():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(approve_upgrade_plan(data.get("plan_id")))


@app.route("/remote/upgrade-planner/reject", methods=["POST"])
def remote_upgrade_planner_reject():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(reject_upgrade_plan(data.get("plan_id"), data.get("reason", "User rejected upgrade plan")))

@app.route("/remote/upgrade-planner/plan/<plan_id>")
def remote_upgrade_planner_get_plan(plan_id):
    p = upgrade_get_plan(plan_id)
    if p:
        return jsonify({"ok": True, "plan": p})
    return jsonify({"ok": False, "error": "not found"}), 404

@app.route("/remote/nous-initiatives")
def remote_nous_initiatives():
    """Unified: all pending proposals NOUS wants executed, ordered by priority."""
    import time as _time
    items = []

    # ── NOUS Drive proposals (self-generated, survival, improvement, curiosity) ─
    try:
        for p in nous_drive_pending():
            items.append({
                "id": str(p["id"]),
                "type": p.get("type", "drive"),
                "priority": p.get("priority", "medium"),
                "icon": p.get("icon", "🤖"),
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "risk": p.get("risk", "low"),
                "created": p.get("created", 0),
                "source": "nous_drive",
                "action": p.get("action", ""),
                "approve_route": "/remote/nous-drive/approve",
                "reject_route":  "/remote/nous-drive/reject",
                "approve_payload": {"proposal_id": p["id"]},
                "reject_payload":  {"proposal_id": p["id"], "reason": "User rejected"},
            })
    except Exception:
        pass

    # ── Upgrade plans ─────────────────────────────────────────────────────────
    try:
        for p in list_upgrade_plans():
            if p.get("status") == "pending":
                upgrades = p.get("upgrades", [])
                detail = "; ".join(u.get("title","") for u in upgrades[:3])
                items.append({
                    "id": str(p["id"]),
                    "type": "upgrade",
                    "priority": "high",
                    "icon": "🚀",
                    "title": p.get("title", "Upgrade Plan"),
                    "description": detail or p.get("description", ""),
                    "risk": "medium",
                    "created": p.get("created", 0),
                    "source": "upgrade_planner",
                    "approve_route": "/remote/upgrade-planner/approve",
                    "reject_route":  "/remote/upgrade-planner/reject",
                    "approve_payload": {"plan_id": p["id"]},
                    "reject_payload":  {"plan_id": p["id"], "reason": "User rejected"},
                })
    except Exception:
        pass

    # ── Mission proposals ─────────────────────────────────────────────────────
    try:
        for p in list_mission_proposals():
            if p.get("status") == "pending":
                items.append({
                    "id": str(p["id"]),
                    "type": "mission",
                    "priority": "medium",
                    "icon": "🎯",
                    "title": p.get("title", "Mission Proposal"),
                    "description": p.get("description", ""),
                    "risk": "low",
                    "created": p.get("created", 0),
                    "source": "mission_planner",
                    "approve_route": "/remote/mission-planner/approve",
                    "reject_route":  "/remote/mission-planner/reject",
                    "approve_payload": {"proposal_id": p["id"]},
                    "reject_payload":  {"proposal_id": p["id"], "reason": "User rejected"},
                })
    except Exception:
        pass

    # ── Repair proposals ──────────────────────────────────────────────────────
    try:
        for p in list_repair_proposals():
            if p.get("status") == "pending":
                items.append({
                    "id": str(p["id"]),
                    "type": "repair",
                    "priority": "high",
                    "icon": "🔧",
                    "title": p.get("title", "Repair Proposal"),
                    "description": p.get("description", ""),
                    "risk": p.get("risk", "medium"),
                    "created": p.get("created", 0),
                    "source": "autonomous_repair",
                    "approve_route": "/remote/autonomous-repair/approve",
                    "reject_route":  "/remote/autonomous-repair/reject",
                    "approve_payload": {"proposal_id": p["id"]},
                    "reject_payload":  {"proposal_id": p["id"], "reason": "User rejected"},
                })
    except Exception:
        pass

    items.sort(key=lambda x: {"high":0,"medium":1,"low":2}.get(x.get("priority","low"),2))
    return jsonify({"ok": True, "initiatives": items, "count": len(items),
                    "drive_status": nous_drive_status()})


# ── NOUS Drive routes ──────────────────────────────────────────────────────────

@app.route("/remote/nous-drive/status")
def remote_nous_drive_status():
    return jsonify(nous_drive_status())

@app.route("/remote/nous-drive/think", methods=["POST"])
def remote_nous_drive_think():
    data = request.get_json(silent=True) or {}
    return jsonify(nous_drive_think(force=data.get("force", True)))

@app.route("/remote/nous-drive/proposals")
def remote_nous_drive_proposals():
    return jsonify(nous_drive_proposals())

@app.route("/remote/nous-drive/approve", methods=["POST"])
def remote_nous_drive_approve():
    data = request.get_json(silent=True) or {}
    return jsonify(nous_drive_approve(data.get("proposal_id")))

@app.route("/remote/nous-drive/proposal/<proposal_id>")
def remote_nous_drive_get_proposal(proposal_id):
    p = nous_drive_get_proposal(proposal_id)
    if p:
        return jsonify({"ok": True, "proposal": p})
    return jsonify({"ok": False, "error": "not found"}), 404

@app.route("/remote/nous-drive/reject", methods=["POST"])
def remote_nous_drive_reject():
    data = request.get_json(silent=True) or {}
    return jsonify(nous_drive_reject(data.get("proposal_id"), data.get("reason","User rejected")))

# ── NOUS Capabilities: Weather ─────────────────────────────────────────────────
@app.route("/nous/weather")
def nous_weather():
    return jsonify(get_weather(request.args.get("refresh","") == "1"))

@app.route("/nous/weather/status")
def nous_weather_status():
    return jsonify(weather_status())

# ── NOUS Capabilities: GPS ─────────────────────────────────────────────────────
@app.route("/nous/gps/update", methods=["POST"])
def nous_gps_update():
    data = request.get_json(silent=True) or {}
    lat, lon = data.get("lat"), data.get("lon")
    if lat is None or lon is None:
        return jsonify({"ok": False, "error": "lat/lon required"}), 400
    fix = gps_update_pos(float(lat), float(lon), data.get("accuracy"), "browser")
    return jsonify({"ok": True, "fix": fix})

@app.route("/nous/gps/status")
def nous_gps_status_route():
    return jsonify(gps_status())

@app.route("/nous/gps/track")
def nous_gps_track():
    limit = int(request.args.get("limit", 100))
    return jsonify({"ok": True, "track": gps_get_track(limit)})

@app.route("/nous/gps/clear", methods=["POST"])
def nous_gps_clear():
    return jsonify(gps_clear_track())

# ── NOUS Capabilities: Voice ───────────────────────────────────────────────────
@app.route("/nous/voice/status")
def nous_voice_status():
    return jsonify(voice_status())

@app.route("/nous/voice/tts", methods=["POST"])
def nous_voice_tts():
    data = request.get_json(silent=True) or {}
    return jsonify(prepare_tts(data.get("text",""), data.get("lang")))

# ── NOUS Capabilities: Web Search ──────────────────────────────────────────────
@app.route("/nous/search", methods=["POST"])
def nous_web_search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")
    if not query:
        return jsonify({"ok": False, "error": "query required"}), 400
    return jsonify(web_search_fn(query, max_results=int(data.get("max_results", 5))))

# ── NOUS Capabilities: Cron Scheduler ─────────────────────────────────────────
@app.route("/nous/cron/status")
def nous_cron_status_route():
    return jsonify(cron_status())

@app.route("/nous/cron/jobs")
def nous_cron_jobs():
    return jsonify({"ok": True, "jobs": cron_list_jobs()})

@app.route("/nous/cron/add", methods=["POST"])
def nous_cron_add():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("action"):
        return jsonify({"ok": False, "error": "name and action required"}), 400
    job = cron_add_job(data["name"], data["action"], int(data.get("hour",8)), int(data.get("minute",0)), data.get("days"))
    return jsonify({"ok": True, "job": job})

@app.route("/nous/cron/remove", methods=["POST"])
def nous_cron_remove():
    data = request.get_json(silent=True) or {}
    return jsonify(cron_remove_job(str(data.get("job_id",""))))

@app.route("/nous/cron/toggle", methods=["POST"])
def nous_cron_toggle():
    data = request.get_json(silent=True) or {}
    return jsonify(cron_toggle_job(str(data.get("job_id","")), bool(data.get("enabled", True))))


@app.route("/remote/nous-initiatives/act", methods=["POST"])
def remote_nous_initiatives_act():
    """Unified approve/reject for any initiative type."""
    import requests as _req
    data = request.get_json(silent=True) or {}
    action  = data.get("action")   # "approve" | "reject"
    route   = data.get("route")
    payload = data.get("payload", {})
    if not route or action not in ("approve","reject"):
        return jsonify({"ok": False, "error": "action and route required"})
    # Internal dispatch — call the route function directly via the app
    with app.test_request_context(route, method="POST",
                                  json=payload,
                                  headers={"X-NOUS-Token": request.headers.get("X-NOUS-Token",""),
                                           "Authorization": request.headers.get("Authorization","")}):
        try:
            resp = app.full_dispatch_request()
            import json as _j
            body = _j.loads(resp.get_data(as_text=True))
            return jsonify({"ok": True, "result": body})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})


@app.route("/remote/deep-code-analyst/status")
def remote_deep_code_analyst_status():
    return jsonify(deep_code_analyst_status())


@app.route("/remote/deep-code-analyst/reports")
def remote_deep_code_analyst_reports():
    return jsonify(list_deep_code_reports())


@app.route("/remote/deep-code-analyst/analyze", methods=["POST"])
def remote_deep_code_analyst_analyze():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(analyze_failure(data.get("problem", data)))


@app.route("/remote/deep-code-analyst/analyze-latest-diagnosis", methods=["POST"])
def remote_deep_code_analyst_latest():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(analyze_latest_diagnosis_deep())


@app.route("/remote/self-healing/status")
def remote_self_healing_status():
    return jsonify(self_healing_status())


@app.route("/remote/self-healing/run-analysis", methods=["POST"])
def remote_self_healing_run_analysis():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_self_healing_analysis(data.get("problem")))


@app.route("/remote/patch-generator/status")
def remote_patch_generator_status():
    return jsonify(patch_generator_status())


@app.route("/remote/patch-generator/proposals")
def remote_patch_generator_proposals():
    return jsonify(list_patch_proposals())


@app.route("/remote/patch-generator/approve", methods=["POST"])
def remote_patch_generator_approve():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(approve_patch_proposal(data.get("proposal_id")))


@app.route("/remote/patch-generator/reject", methods=["POST"])
def remote_patch_generator_reject():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(reject_patch_proposal(
        data.get("proposal_id"),
        data.get("reason", "User rejected patch proposal")
    ))

@app.route("/remote/command-center/status")
def remote_command_center_status():
    return jsonify(executive_command_center_status())


@app.route("/remote/command-center/run-cycle", methods=["POST"])
def remote_command_center_run_cycle():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_executive_command_cycle(data.get("trigger", "dashboard")))

@app.route("/remote/executive-loop-v2/status")
def remote_executive_loop_v2_status():
    return jsonify(executive_loop_v2_status())


@app.route("/remote/executive-loop-v2/run", methods=["POST"])
def remote_executive_loop_v2_run():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_executive_loop_v2(data.get("trigger", "dashboard")))


@app.route("/remote/pending-review/status")
def remote_pending_review_status():
    return jsonify(pending_review_status())

@app.route("/remote/code-analyst/status")
def remote_code_analyst_status():
    return jsonify(code_analyst_status())


@app.route("/remote/code-analyst/reports")
def remote_code_analyst_reports():
    return jsonify(list_code_analysis_reports())


@app.route("/remote/code-analyst/analyze", methods=["POST"])
def remote_code_analyst_analyze():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(analyze_problem(data.get("problem", data)))


@app.route("/remote/code-analyst/analyze-latest-diagnosis", methods=["POST"])
def remote_code_analyst_latest():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(analyze_latest_diagnosis())


@app.route("/remote/code-analyst/patch-suggestion", methods=["POST"])
def remote_code_analyst_patch_suggestion():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(generate_patch_suggestion(data.get("problem", data)))


@app.route("/remote/auto-mission-scheduler/status")
def remote_auto_mission_scheduler_status():
    return jsonify(auto_mission_scheduler_status())


@app.route("/remote/auto-mission-scheduler/start", methods=["POST"])
def remote_auto_mission_scheduler_start():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(start_auto_mission_scheduler(data.get("interval_seconds", 900)))


@app.route("/remote/auto-mission-scheduler/stop", methods=["POST"])
def remote_auto_mission_scheduler_stop():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(stop_auto_mission_scheduler())


@app.route("/remote/auto-mission-scheduler/run-once", methods=["POST"])
def remote_auto_mission_scheduler_run_once():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(run_auto_mission_scheduler_once())

@app.route("/remote/auto-mission-executor/status")
def remote_auto_mission_executor_status():
    return jsonify(auto_mission_executor_status())


@app.route("/remote/auto-mission-executor/run", methods=["POST"])
def remote_auto_mission_executor_run():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_auto_mission_executor(
        data.get("max_missions", 1),
        data.get("max_steps_per_mission", 3),
        data.get("trigger", "manual")
    ))


@app.route("/remote/auto-mission-executor/enable", methods=["POST"])
def remote_auto_mission_executor_enable():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(set_auto_mission_executor_enabled(True))


@app.route("/remote/auto-mission-executor/disable", methods=["POST"])
def remote_auto_mission_executor_disable():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(set_auto_mission_executor_enabled(False))

@app.route("/remote/autonomous-repair/status")
def remote_autonomous_repair_status():
    return jsonify(repair_status())


@app.route("/remote/autonomous-repair/proposals")
def remote_autonomous_repair_proposals():
    return jsonify(list_repair_proposals())


@app.route("/remote/autonomous-repair/propose", methods=["POST"])
def remote_autonomous_repair_propose():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(propose_repair_from_diagnosis())


@app.route("/remote/autonomous-repair/approve", methods=["POST"])
def remote_autonomous_repair_approve():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(approve_repair_proposal(data.get("proposal_id")))


@app.route("/remote/autonomous-repair/reject", methods=["POST"])
def remote_autonomous_repair_reject():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(reject_repair_proposal(
        data.get("proposal_id"),
        data.get("reason", "User rejected repair proposal")
    ))

# ── Safety Net / Circuit Breaker ─────────────────────────────────────────────

@app.route("/remote/safety/status")
def remote_safety_status():
    from executor.safety_net import safety_status
    return jsonify(safety_status())

@app.route("/remote/safety/incidents")
def remote_safety_incidents():
    from executor.safety_net import list_incidents
    limit = int(request.args.get("limit", 40))
    return jsonify({"ok": True, "incidents": list_incidents(limit)})

@app.route("/remote/safety/circuit-reset", methods=["POST"])
def remote_safety_circuit_reset():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    from executor.safety_net import reset_circuit
    return jsonify(reset_circuit())

@app.route("/remote/safety/rollback", methods=["POST"])
def remote_safety_rollback():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    incident_id = data.get("incident_id", "")
    if not incident_id:
        return jsonify({"ok": False, "error": "Δεν δόθηκε incident_id"})
    from executor.safety_net import manual_rollback
    return jsonify(manual_rollback(incident_id))

@app.route("/remote/self-diagnosis/status")
def remote_self_diagnosis_status():
    return jsonify(self_diagnosis_status())


@app.route("/remote/self-diagnosis/run", methods=["POST"])
def remote_self_diagnosis_run():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(run_self_diagnosis())


@app.route("/remote/self-diagnosis/apply-fix", methods=["POST"])
def remote_self_diagnosis_apply_fix():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(apply_safe_self_fix(data.get("fix_id")))

@app.route("/remote/self-diagnosis/ai-analyze", methods=["POST"])
def remote_self_diagnosis_ai_analyze():
    from executor.self_diagnosis import ai_analyze_diagnosis
    return jsonify(ai_analyze_diagnosis())

@app.route("/remote/dashboard-action-audit")
def remote_dashboard_action_audit():
    from executor.security import TOKEN
    return jsonify(dashboard_action_audit(app, TOKEN))

@app.route("/remote/mission-planner/status")
def remote_mission_planner_status():
    return jsonify(mission_planner_status())


@app.route("/remote/mission-planner/proposals")
def remote_mission_planner_proposals():
    return jsonify(list_mission_proposals())


@app.route("/remote/mission-planner/propose", methods=["POST"])
def remote_mission_planner_propose():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(propose_mission_for_goal(data.get("goal_id")))


@app.route("/remote/mission-planner/approve", methods=["POST"])
def remote_mission_planner_approve():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(approve_mission_proposal(data.get("proposal_id")))


@app.route("/remote/mission-planner/reject", methods=["POST"])
def remote_mission_planner_reject():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(reject_mission_proposal(
        data.get("proposal_id"),
        data.get("reason", "User rejected mission proposal")
    ))

@app.route("/remote/goal-progress-intelligence/status")
def remote_goal_progress_intelligence_status():
    return jsonify(goal_progress_intelligence_status())


@app.route("/remote/goal-progress-intelligence/analyze")
def remote_goal_progress_intelligence_analyze():
    return jsonify(analyze_goal_progress())


@app.route("/remote/goal-progress-intelligence/apply", methods=["POST"])
def remote_goal_progress_intelligence_apply():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(apply_goal_progress_intelligence())

@app.route("/remote/executive-scheduler-loop/status")
def remote_executive_scheduler_loop_status():
    return jsonify(scheduler_loop_status())


@app.route("/remote/executive-scheduler-loop/start", methods=["POST"])
def remote_executive_scheduler_loop_start():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(start_scheduler_loop(data.get("interval_seconds", 1800)))


@app.route("/remote/executive-scheduler-loop/stop", methods=["POST"])
def remote_executive_scheduler_loop_stop():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(stop_scheduler_loop())


@app.route("/remote/executive-scheduler-loop/run-once", methods=["POST"])
def remote_executive_scheduler_loop_run_once():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(run_scheduler_once())

@app.route("/remote/executive-scheduler/status")
def remote_executive_scheduler_status():
    return jsonify(executive_scheduler_status())


@app.route("/remote/executive-scheduler/reviews")
def remote_executive_scheduler_reviews():
    return jsonify(list_executive_reviews())


@app.route("/remote/executive-scheduler/run-review", methods=["POST"])
def remote_executive_scheduler_run_review():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_executive_review(data.get("trigger", "manual")))

@app.route("/remote/executive-intelligence/execute-recommendation", methods=["POST"])
def remote_execute_recommendation():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(execute_recommendation(data.get("index", 0)))


@app.route("/remote/executive-intelligence/reject-recommendation", methods=["POST"])
def remote_reject_recommendation():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(reject_recommendation(
        data.get("index", 0),
        data.get("reason", "User rejected recommendation")
    ))

@app.route("/remote/executive-intelligence/status")
def remote_executive_intelligence_status():
    return jsonify(executive_intelligence_status())


@app.route("/remote/executive-intelligence/report")
def remote_executive_intelligence_report():
    return jsonify(executive_intelligence_report())

@app.route("/remote/lessons/status")
def remote_lessons_status():
    return jsonify(lesson_status())


@app.route("/remote/lessons/list")
def remote_lessons_list():
    return jsonify(list_lessons())


@app.route("/remote/lessons/search", methods=["POST"])
def remote_lessons_search():
    data = request.get_json(silent=True) or {}
    return jsonify(search_lessons(data.get("query", "")))


@app.route("/remote/lessons/record", methods=["POST"])
def remote_lessons_record():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(record_lesson(
        lesson=data.get("lesson", ""),
        outcome=data.get("outcome", "success"),
        goal_id=data.get("goal_id"),
        mission_id=data.get("mission_id"),
        decision_id=data.get("decision_id"),
        confidence=data.get("confidence", 0.8),
        tags=data.get("tags", []),
    ))

@app.route("/remote/decision-memory/status")
def remote_decision_memory_status_route():
    return jsonify(decision_status())


@app.route("/remote/decision-memory/list")
def remote_decision_memory_list_route():
    return jsonify(list_decisions())


@app.route("/remote/decision-memory/search", methods=["POST"])
def remote_decision_memory_search_route():
    data = request.get_json(silent=True) or {}
    return jsonify(search_decisions(data.get("query", ""), data.get("limit", 20)))


@app.route("/remote/decision-memory/record", methods=["POST"])
def remote_decision_memory_record_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(record_decision(
        title=data.get("title", "Untitled decision"),
        reason=data.get("reason", ""),
        goal_id=data.get("goal_id"),
        mission_id=data.get("mission_id"),
        action=data.get("action"),
        result=data.get("result"),
        confidence=data.get("confidence", 0.7),
        tags=data.get("tags", []),
    ))

@app.route("/remote/brain-restore/status")
def remote_brain_restore_status_route():
    return jsonify(restore_status())


@app.route("/remote/brain-restore/inspect", methods=["POST"])
def remote_brain_restore_inspect_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(inspect_brain_backup(data.get("path", "")))


@app.route("/remote/brain-restore/apply", methods=["POST"])
def remote_brain_restore_apply_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(restore_brain_backup(
        data.get("path", ""),
        bool(data.get("apply", False))
    ))

@app.route("/remote/brain-backup/status")
def remote_brain_backup_status_route():
    return jsonify(brain_backup_status())


@app.route("/remote/brain-backup/list")
def remote_brain_backup_list_route():
    return jsonify(list_brain_backups())


@app.route("/remote/brain-backup/create", methods=["POST"])
def remote_brain_backup_create_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(create_brain_backup())

@app.route("/remote/brain/status")
def remote_brain_status_route():
    return jsonify(brain_status())


@app.route("/remote/brain/state")
def remote_brain_state_route():
    return jsonify(build_brain_state())


@app.route("/remote/brain/save", methods=["POST"])
def remote_brain_save_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(save_brain_state())


@app.route("/remote/brain/load")
def remote_brain_load_route():
    return jsonify(load_brain_state())

@app.route("/remote/goals-v2/status")
def remote_goals_v2_status_route():
    return jsonify(goal_status())


@app.route("/remote/goals-v2")
def remote_goals_v2_list_route():
    return jsonify(list_goals())


@app.route("/remote/goals-v2/seed", methods=["POST"])
def remote_goals_v2_seed_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(seed_core_goals())


@app.route("/remote/goals-v2/create", methods=["POST"])
def remote_goals_v2_create_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(create_goal(
        data.get("title", "Untitled goal"),
        data.get("description", ""),
        data.get("priority", 3),
    ))


@app.route("/remote/goals-v2/note", methods=["POST"])
def remote_goals_v2_note_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(add_goal_note(data.get("id"), data.get("note", "")))


@app.route("/remote/goals-v2/link-mission", methods=["POST"])
def remote_goals_v2_link_mission_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(link_mission_to_goal(data.get("goal_id"), data.get("mission_id")))


@app.route("/remote/goals-v2/refresh", methods=["POST"])
def remote_goals_v2_refresh_route():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    goal_id = data.get("id")
    try:
        result = refresh_goal_progress(goal_id) if goal_id else refresh_goal_progress()
    except TypeError:
        try:
            result = refresh_goal_progress()
        except Exception as e:
            result = {"ok": False, "error": str(e)}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    return jsonify(result)


@app.route("/remote/goals-v2/create-mission", methods=["POST"])
def remote_goals_v2_create_mission_route():
    if not check_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(create_goal_mission(
        data.get("goal_id"),
        data.get("title", "Goal mission"),
        data.get("description", ""),
        data.get("tasks", []),
    ))

@app.route("/remote/executive/status")
def remote_executive_status_route():
    return jsonify(executive_status())


@app.route("/remote/executive/plan", methods=["POST"])
def remote_executive_plan_route():
    data = request.get_json(silent=True) or {}
    return jsonify(executive_plan(data.get("prompt", "")))


@app.route("/remote/executive/run", methods=["POST"])
def remote_executive_run_route():
    data = request.get_json(silent=True) or {}
    return jsonify(executive_run(
        data.get("prompt", ""),
        data.get("max_steps", 3),
        bool(data.get("execute", True))
    ))

@app.route("/remote/workspace/status")
def remote_workspace_status_route():
    return jsonify(workspace_status())


@app.route("/remote/workspace/plan", methods=["POST"])
def remote_workspace_plan_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(plan_from_prompt(data.get("prompt", "")))


@app.route("/remote/workspace/create-mission", methods=["POST"])
def remote_workspace_create_mission_route():
    data = request.get_json(silent=True) or {}
    return jsonify(create_workspace_mission(data.get("prompt", "")))


@app.route("/remote/workspace/run-mission", methods=["POST"])
def remote_workspace_run_mission_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_workspace_mission(data.get("id"), data.get("max_steps", 3)))

@app.route("/remote/missions/status")
def remote_missions_status_route():
    return jsonify(mission_status())


@app.route("/remote/missions")
def remote_missions_list_route():
    return jsonify(list_missions())


@app.route("/remote/missions/create", methods=["POST"])
def remote_missions_create_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(create_mission(
        data.get("title", "Untitled mission"),
        data.get("description", ""),
        data.get("tasks", [])
    ))


@app.route("/remote/missions/create-standard", methods=["POST"])
def remote_missions_create_standard_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(create_standard_mission(data.get("kind", "system_check")))


@app.route("/remote/missions/run-next", methods=["POST"])
def remote_missions_run_next_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(run_next_mission_task(data.get("id")))


@app.route("/remote/missions/run-cycle", methods=["POST"])
def remote_missions_run_cycle_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(run_mission_cycle(data.get("id"), data.get("max_steps", 3)))



@app.route("/remote/missions/approvals")
def remote_missions_approvals_route():
    return jsonify(pending_approvals())

@app.route("/remote/missions/approve-task", methods=["POST"])
def remote_missions_approve_task_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(approve_task(data.get("mission_id"), data.get("task_id")))

@app.route("/remote/ops/status")
def remote_ops_status_route():
    return jsonify(ops_status())


@app.route("/remote/ops/run", methods=["POST"])
def remote_ops_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(run_ops_action(
        data.get("action", ""),
        data.get("payload", {})
    ))

@app.route("/remote/companion/status")
def remote_companion_status_route():
    return jsonify(companion_status())


@app.route("/remote/companion/home", methods=["POST"])
def remote_companion_home_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(companion_home())


@app.route("/remote/companion/back", methods=["POST"])
def remote_companion_back_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(companion_back())


@app.route("/remote/companion/ui-tree", methods=["POST"])
def remote_companion_ui_tree_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(companion_ui_tree())


@app.route("/remote/companion/tap", methods=["POST"])
def remote_companion_tap_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(companion_tap(data.get("x", 0), data.get("y", 0)))

@app.route("/remote/device-control/status")
def remote_device_control_status_route():
    return jsonify(device_control_status())


@app.route("/remote/device-control/recommendation")
def remote_device_control_recommendation_route():
    return jsonify(device_control_recommendation())

@app.route("/remote/operator-backend/status")
def remote_operator_backend_status_route():
    return jsonify(operator_backend_status())


@app.route("/remote/operator-backend/browser")
def remote_operator_backend_browser_route():
    return jsonify(browser_backend_status())


@app.route("/remote/operator-backend/android")
def remote_operator_backend_android_route():
    return jsonify(android_backend_status())


@app.route("/remote/operator-backend/deploy")
def remote_operator_backend_deploy_route():
    return jsonify(deployment_backend_status())


@app.route("/remote/browser-bridge/status")
def remote_browser_bridge_status_route():
    return jsonify(remote_browser_bridge_status())


@app.route("/remote/browser-bridge/jobs")
def remote_browser_bridge_jobs_route():
    return jsonify(list_browser_jobs())


@app.route("/remote/browser-bridge/create", methods=["POST"])
def remote_browser_bridge_create_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(create_browser_job(
        data.get("url", ""),
        data.get("actions", []),
        data.get("reason", "remote browser required")
    ))


@app.route("/remote/browser-bridge/complete", methods=["POST"])
def remote_browser_bridge_complete_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(complete_browser_job(
        data.get("id"),
        data.get("result", {})
    ))

@app.route("/remote/operator/capabilities")
def remote_operator_capabilities_route():
    return jsonify(operator_capability_status())


@app.route("/remote/operator/reality-flags")
def remote_operator_reality_flags_route():
    return jsonify(reality_flags())


@app.route("/remote/browser-driver/status")
def remote_browser_driver_status_route():
    return jsonify(browser_driver_status())


@app.route("/remote/browser-driver/run", methods=["POST"])
def remote_browser_driver_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_browser_actions(data.get("url", ""), data.get("actions", [])))



@app.route("/remote/vercel/status")
def remote_vercel_status_route():
    return jsonify(vercel_status())


@app.route("/remote/vercel/deploy", methods=["POST"])
def remote_vercel_deploy_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(vercel_deploy(
        data.get("path", ""),
        bool(data.get("prod", True))
    ))

@app.route("/remote/deploy/providers")
def remote_deploy_providers_route():
    return jsonify(deploy_provider_status())


@app.route("/remote/deploy/provider-run", methods=["POST"])
def remote_deploy_provider_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(deploy_with_provider(data.get("provider", ""), data.get("path", ".")))

@app.route("/remote/real-actions/status")
def remote_real_actions_status_route():
    return jsonify(real_actions_status())


@app.route("/remote/real-actions/run", methods=["POST"])
def remote_real_actions_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_real_action(data.get("action", ""), data.get("payload", {})))


@app.route("/remote/real-chain/status")
def remote_real_chain_status_route():
    return jsonify(real_chain_status())


@app.route("/remote/real-chain/run", methods=["POST"])
def remote_real_chain_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_real_chain(data.get("steps", [])))

@app.route("/remote/reality/status")
def remote_reality_status_route():
    return jsonify(reality_status())

@app.route("/remote/operator/status")
def remote_operator_status_route():
    return jsonify({
        "browser": browser_operator_status(),
        "android": android_operator_status(),
        "deploy": deploy_operator_status(),
        "approvals": list_approvals()
    })


@app.route("/remote/operator/approvals")
def remote_operator_approvals_route():
    return jsonify(list_approvals())


@app.route("/remote/operator/approve", methods=["POST"])
def remote_operator_approve_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(approve(data.get("id")))


@app.route("/remote/operator/reject", methods=["POST"])
def remote_operator_reject_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(reject(data.get("id")))


@app.route("/remote/operator/browser/open", methods=["POST"])
def remote_operator_browser_open_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(operator_open_url(data.get("url", "")))


@app.route("/remote/operator/browser/click", methods=["POST"])
def remote_operator_browser_click_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(prepare_click(data.get("url", ""), data.get("selector", ""), data.get("approval_id")))


@app.route("/remote/operator/browser/fill-form", methods=["POST"])
def remote_operator_browser_fill_form_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(prepare_fill_form(data.get("url", ""), data.get("fields", {}), data.get("approval_id")))


@app.route("/remote/operator/browser/login", methods=["POST"])
def remote_operator_browser_login_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(prepare_login(data.get("url", ""), data.get("username_field", "username"), data.get("password_field", "password")))


@app.route("/remote/operator/android/tap", methods=["POST"])
def remote_operator_android_tap_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(android_tap(data.get("x", 0), data.get("y", 0), data.get("approval_id")))


@app.route("/remote/operator/android/swipe", methods=["POST"])
def remote_operator_android_swipe_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(android_swipe(data.get("x1", 0), data.get("y1", 0), data.get("x2", 0), data.get("y2", 0), data.get("duration", 300), data.get("approval_id")))


@app.route("/remote/operator/android/keyevent", methods=["POST"])
def remote_operator_android_keyevent_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(android_keyevent(data.get("name", "")))


@app.route("/remote/operator/deploy", methods=["POST"])
def remote_operator_deploy_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(prepare_real_deploy(data.get("provider", ""), data.get("app", ""), data.get("approval_id")))

@app.route("/remote/hands/status")
def remote_hands_status_route():
    return jsonify({
        "browser": browser_status(),
        "android": android_actions_status(),
        "deploy": deploy_status(),
        "git": git_workflow_status(),
        "complex": complex_action_status()
    })


@app.route("/remote/browser/search", methods=["POST"])
def remote_browser_search_v2_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(browser_search(data.get("query", "")))


@app.route("/remote/browser/read-url", methods=["POST"])
def remote_browser_read_v2_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(browser_read(data.get("url", "")))


@app.route("/remote/android/action", methods=["POST"])
def remote_android_action_v2_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_android_action(data.get("action", ""), data.get("payload", {})))


@app.route("/remote/deploy/status")
def remote_deploy_status_route():
    return jsonify(deploy_status())


@app.route("/remote/deploy/local", methods=["POST"])
def remote_deploy_local_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(register_local_deploy(data.get("app", "")))


@app.route("/remote/git/status")
def remote_git_status_route():
    return jsonify(git_workflow_status())


@app.route("/remote/git/checkpoint", methods=["POST"])
def remote_git_checkpoint_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(git_safe_checkpoint(data.get("message", "NOUS checkpoint")))


@app.route("/remote/complex/status")
def remote_complex_status_route():
    return jsonify(complex_action_status())


@app.route("/remote/complex/run", methods=["POST"])
def remote_complex_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(run_complex_action(data.get("steps", [])))

@app.route("/remote/team/status")
def remote_team_status_route():
    return jsonify(team_status())


@app.route("/remote/team/cycle", methods=["POST"])
def remote_team_cycle_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(team_cycle(bool(data.get("real_research", False))))


@app.route("/remote/internet-learning/status")
def remote_internet_learning_status_route():
    return jsonify(internet_learning_status())


@app.route("/remote/internet-learning/topic", methods=["POST"])
def remote_internet_learning_topic_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(internet_learn_topic(
        data.get("topic"),
        data.get("query")
    ))


@app.route("/remote/internet-learning/url", methods=["POST"])
def remote_internet_learning_url_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(internet_learn_url(
        data.get("url", ""),
        data.get("topic")
    ))

@app.route("/remote/self-improve/status")
def remote_self_improve_status_route():
    return jsonify(self_improvement_status())


@app.route("/remote/self-improve/patches")
def remote_self_improve_patches_route():
    return jsonify(list_patches())


@app.route("/remote/self-improve/create-patch", methods=["POST"])
def remote_self_improve_create_patch_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(create_patch_request(
        data.get("file", ""),
        data.get("content", ""),
        data.get("reason", "remote")
    ))


@app.route("/remote/self-improve/apply-patch", methods=["POST"])
def remote_self_improve_apply_patch_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(apply_patch(data.get("id")))

@app.route("/remote/master/status")
def remote_master_status_route():
    return jsonify(master_state())


@app.route("/remote/master/priority")
def remote_master_priority_route():
    return jsonify(choose_master_priority())


@app.route("/remote/master/cycle", methods=["POST"])
def remote_master_cycle_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(master_cycle(bool(data.get("real_research", False))))


@app.route("/remote/guardian/policy")
def remote_guardian_policy_route():
    return jsonify(policy_status())


@app.route("/remote/guardian/check", methods=["POST"])
def remote_guardian_check_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(check_action(data.get("action", ""), data.get("payload", {})))


@app.route("/remote/research/status")
def remote_real_research_status_route():
    return jsonify(research_status())


@app.route("/remote/research/learned")
def remote_real_research_learned_route():
    return jsonify(learned_items())


@app.route("/remote/research/learn-topic", methods=["POST"])
def remote_real_research_learn_topic_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(research_to_knowledge(data.get("topic")))

@app.route("/remote/agent/decide")
def remote_agent_decide_route():
    return jsonify(decide_next_action())


@app.route("/remote/agent/act", methods=["POST"])
def remote_agent_act_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(agent_act_cycle())


@app.route("/remote/agent/goals")
def remote_agent_goals_route():
    return jsonify(prioritize_goals())


@app.route("/remote/agent/journal")
def remote_agent_journal_route():
    return jsonify(list_journal())

@app.route("/remote/local-llm/status")
def remote_local_llm_status_route():
    return jsonify(local_llm_status())


@app.route("/remote/local-llm/ask", methods=["POST"])
def remote_local_llm_ask_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(ask_local(data.get("prompt", ""), int(data.get("timeout", 60))))


@app.route("/remote/app-evolver/status")
def remote_app_evolver_status_route():
    return jsonify(app_evolution_status())


@app.route("/remote/app-evolver/queue", methods=["POST"])
def remote_app_evolver_queue_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(queue_app_improvement(
        data.get("app", ""),
        data.get("request", "βελτίωσε την εφαρμογή"),
        int(data.get("priority", 4))
    ))


@app.route("/remote/android/open-url", methods=["POST"])
def remote_android_open_url_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(android_open_url(data.get("url", "")))

@app.route("/remote/code/health")
def remote_code_health_route():
    return jsonify(code_health())


@app.route("/remote/code/advice")
def remote_code_advice_route():
    return jsonify(code_advice())


@app.route("/remote/app-factory/status")
def remote_app_factory_status_route():
    return jsonify(app_factory_status())


@app.route("/remote/app-factory/create", methods=["POST"])
def remote_app_factory_create_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(create_app_from_idea(data.get("idea", "")))


@app.route("/remote/app-factory/queue", methods=["POST"])
def remote_app_factory_queue_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(queue_app_idea(
        data.get("idea", ""),
        int(data.get("priority", 4))
    ))


@app.route("/remote/android/status")
def remote_android_status_route():
    return jsonify(android_status())


@app.route("/remote/android/safe-commands")
def remote_android_safe_commands_route():
    return jsonify(android_safe_commands())


@app.route("/remote/android/notify", methods=["POST"])
def remote_android_notify_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(android_notify(
        data.get("title", "ΝΟΥΣ AI"),
        data.get("message", "Ο ΝΟΥΣ είναι ενεργός")
    ))

@app.route("/remote/learning/status")
def remote_learning_status_route():
    return jsonify(learning_status())


@app.route("/remote/learning/run", methods=["POST"])
def remote_learning_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    max_topics = int(data.get("max_topics", 1))
    research = bool(data.get("research", False))

    return jsonify(learning_run(max_topics=max_topics, research=research))


@app.route("/remote/research/next", methods=["POST"])
def remote_research_next_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(research_next_topic())


@app.route("/remote/research/cycle", methods=["POST"])
def remote_research_cycle_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    max_topics = int(data.get("max_topics", 1))
    return jsonify(learning_cycle(max_topics=max_topics))

@app.route("/remote/knowledge")
def remote_knowledge_route():
    return jsonify(knowledge_status())


@app.route("/remote/knowledge/queue")
def remote_knowledge_queue_route():
    return jsonify(load_queue())


@app.route("/remote/knowledge/base")
def remote_knowledge_base_route():
    return jsonify(load_knowledge())


@app.route("/remote/knowledge/cycle", methods=["POST"])
def remote_knowledge_cycle_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(curiosity_cycle())


@app.route("/remote/knowledge/add", methods=["POST"])
def remote_knowledge_add_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(add_topic(
        data.get("topic", ""),
        data.get("reason", "manual"),
        data.get("priority", 5),
        "remote"
    ))


@app.route("/remote/knowledge/learned", methods=["POST"])
def remote_knowledge_learned_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(mark_learned(
        data.get("topic", ""),
        data.get("summary", ""),
        data.get("source", "remote")
    ))

@app.route("/remote/metrics")
def remote_metrics_route():
    return jsonify(collect_metrics())


@app.route("/remote/service/watchdog")
def remote_service_watchdog_route():
    return jsonify(watchdog_check())


@app.route("/remote/queue/retry-failed", methods=["POST"])
def remote_queue_retry_failed_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(retry_failed())


@app.route("/remote/queue/recover-dead", methods=["POST"])
def remote_queue_recover_dead_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(recover_dead_tasks())

@app.route("/remote/projects")
def remote_projects_route():
    return jsonify(list_progress())


@app.route("/remote/projects/summary")
def remote_projects_summary_route():
    return jsonify(project_summary())


@app.route("/remote/projects/sync", methods=["POST"])
def remote_projects_sync_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(sync_projects())


@app.route("/remote/projects/mark-step", methods=["POST"])
def remote_projects_mark_step_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    return jsonify(mark_step(
        data.get("project", ""),
        data.get("step", ""),
        data.get("status", "done")
    ))


@app.route("/remote/self-heal/check", methods=["POST"])
def remote_self_heal_check_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(self_heal_check())

@app.route("/remote/queue")
def remote_queue_route():
    return jsonify(list_queue())


@app.route("/remote/queue/clear", methods=["POST"])
def remote_queue_clear_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(clear_queue())


@app.route("/remote/goals/run", methods=["POST"])
def remote_goals_run_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(goal_executor_cycle())

@app.route("/remote/service/status")
def remote_service_status_route():
    return jsonify(service_status())


@app.route("/remote/service/enable", methods=["POST"])
def remote_service_enable_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    interval = int(data.get("interval", 300))
    return jsonify(service_enable(interval))


@app.route("/remote/service/disable", methods=["POST"])
def remote_service_disable_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(service_disable())


@app.route("/remote/service/run-once", methods=["POST"])
def remote_service_run_once_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(service_run_cycle())

@app.route("/remote/autonomy/start", methods=["POST"])
def remote_autonomy_start_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"result": autonomy_state.start()})


@app.route("/remote/autonomy/stop", methods=["POST"])
def remote_autonomy_stop_route():
    if not check_admin_token(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"result": autonomy_state.stop()})


@app.route("/remote/autonomy/status")
def remote_autonomy_status_route():
    return jsonify(autonomy_state.status())

@app.route("/remote/status")
def remote_status_route():
    from executor.scheduler_agent import list_schedules
    from executor.battery_guard import battery_guard
    from executor.agent_review import review_last

    def safe(fn, fallback=None):
        try:
            return fn()
        except Exception as e:
            return {"error": str(e)} if fallback is None else fallback

    return jsonify({
        "system": "NOUS AI OS",
        "level": 22,
        "battery": safe(battery_guard, {}),
        "autonomy": safe(autonomy_state.status, {}),
        "service": safe(service_status, {}),
        "schedules": safe(list_schedules, []),
        "queue": safe(list_queue, []),
        "projects_progress": safe(project_summary, {}),
        "metrics": safe(collect_metrics, {}),
        "knowledge": safe(knowledge_status, {}),
        "learning": safe(learning_status, {}),
        "code": safe(code_health, {}),
        "app_factory": safe(app_factory_status, {}),
        "app_evolver": safe(app_evolution_status, {}),
        "local_llm": safe(local_llm_status, {}),
        "agent": safe(decide_next_action, {}),
        "master": safe(master_state, {}),
        "guardian": safe(policy_status, {}),
        "self_improvement": safe(self_improvement_status, {}),
        "team": safe(team_status, {}),
        "internet_learning": safe(internet_learning_status, {}),
        "hands": {
            "browser": safe(browser_status, {}),
            "android": safe(android_actions_status, {}),
            "deploy": safe(deploy_status, {}),
            "complex": safe(complex_action_status, {}),
        },
        "real_actions": safe(real_actions_status, {}),
        "progress": safe(progress_snapshot, {}),
        "goal_progress": safe(goal_progress_summary, {}),
        "android": safe(android_safe_commands, []),
        "active_learning_topics": safe(active_learning_topics, []),
        "review": safe(review_last, {}),
        "time": time.time(),
        "tokens": safe(token_stats, {}),
    })


@app.route("/dashboard")
def dashboard():
    return nous_dashboard_html()

@app.route("/apps")
def apps_list():
    return jsonify(list_apps())

@app.route("/apps/<name>/")
def open_generated_app(name):
    abs_dir = os.path.join(os.getcwd(), "generated_apps", name)
    return send_from_directory(abs_dir, "index.html")

@app.route("/apps/<name>/<path:filename>")
def open_generated_app_asset(name, filename):
    abs_dir = os.path.join(os.getcwd(), "generated_apps", name)
    return send_from_directory(abs_dir, filename)

# ── App Builder API ─────────────────────────────────────────────────────────

@app.route("/remote/app-builder/status")
def app_builder_status_route():
    from executor.app_builder import status as _status
    return jsonify(_status())

@app.route("/remote/app-builder/list")
def app_builder_list_route():
    return jsonify({"ok": True, "builds": list_builds()})

@app.route("/remote/app-builder/plan", methods=["POST"])
def app_builder_plan_route():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"ok": False, "error": "description required"})
    result = plan_app(description)
    return jsonify(result)

@app.route("/remote/app-builder/approve", methods=["POST"])
def app_builder_approve_route():
    data = request.get_json(silent=True) or {}
    plan_id = data.get("plan_id", "").strip()
    if not plan_id:
        return jsonify({"ok": False, "error": "plan_id required"})
    result = approve_and_write(plan_id)
    return jsonify(result)

@app.route("/remote/app-builder/reject", methods=["POST"])
def app_builder_reject_route():
    data = request.get_json(silent=True) or {}
    plan_id = data.get("plan_id", "").strip()
    if not plan_id:
        return jsonify({"ok": False, "error": "plan_id required"})
    result = reject_plan(plan_id)
    return jsonify(result)

@app.route("/remote/app-builder/get/<plan_id>")
def app_builder_get_route(plan_id):
    build = get_build(plan_id)
    if not build:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "build": build})


@app.route("/remote/app-builder/files")
def app_builder_files_route():
    """Browse the apps/ folder — list all built app directories and their files."""
    from pathlib import Path as _Path
    apps_dir = _Path("apps")
    if not apps_dir.exists():
        return jsonify({"ok": True, "apps": [], "total": 0, "path": "apps/"})
    apps = []
    for entry in sorted(apps_dir.iterdir()):
        if entry.is_dir():
            files = []
            try:
                for f in sorted(entry.rglob("*")):
                    if f.is_file():
                        size = f.stat().st_size
                        files.append({
                            "name": str(f.relative_to(entry)),
                            "size": size,
                            "size_kb": round(size / 1024, 1),
                        })
            except Exception:
                pass
            # Detect run command from main.py / app.py / requirements.txt
            run_cmd = _detect_run_command(entry)
            apps.append({
                "name": entry.name,
                "path": str(entry),
                "file_count": len(files),
                "files": files[:30],
                "run_command": run_cmd,
            })
    return jsonify({"ok": True, "apps": apps, "total": len(apps), "path": "apps/"})


def _detect_run_command(app_dir) -> str:
    from pathlib import Path as _P
    p = _P(app_dir)
    for candidate in ["main.py", "app.py", "run.py", "server.py"]:
        if (p / candidate).exists():
            return f"python apps/{p.name}/{candidate}"
    return f"python apps/{p.name}/main.py"


# ── In-memory store for running app subprocesses ──────────────────────────────
_running_apps: dict = {}   # app_name -> {"pid": int, "proc": Popen, "port": int, "log": str}


@app.route("/remote/app-builder/read-file")
def app_builder_read_file_route():
    """Return the text content of a file inside apps/<app>/<file>."""
    from pathlib import Path as _P
    app_name = request.args.get("app", "").strip()
    filename = request.args.get("file", "").strip()
    if not app_name or not filename:
        return jsonify({"ok": False, "error": "app and file params required"})
    # Security: no path traversal
    base = _P("apps") / app_name
    target = (base / filename).resolve()
    if not str(target).startswith(str(base.resolve())):
        return jsonify({"ok": False, "error": "invalid path"})
    if not target.exists() or not target.is_file():
        return jsonify({"ok": False, "error": "file not found"})
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return jsonify({"ok": True, "content": content, "file": filename, "app": app_name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def _try_autorepair_app(app_dir) -> dict:
    """
    Autonomous self-repair: scan all .py files in an app directory.
    If a file is a JSON blob (NOUS plan artifact), extract the real Python code and overwrite it.
    Returns {"repaired": bool, "files": [...], "message": str}
    """
    import re as _re
    from pathlib import Path as _P
    repaired_files = []
    p = _P(app_dir)
    for pyfile in p.rglob("*.py"):
        try:
            raw = pyfile.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # Detect JSON blob (NOUS plan artifact starts with ```json or { with "files" key)
        is_json_blob = raw.strip().startswith("```json") or (
            raw.strip().startswith("{") and '"files"' in raw and '"content"' in raw
        )
        if not is_json_blob:
            continue
        # --- Auto-repair: extract real Python from the JSON blob ---
        extracted = None
        # Try to extract from "content": "..." field (JSON-escaped Python)
        m = _re.search(r'"content":\s*"(.*?)(?<!\\)"\s*[,\}]', raw, _re.DOTALL)
        if m:
            code = m.group(1)
            code = (code.replace("\\n", "\n").replace("\\t", "\t")
                       .replace('\\"', '"').replace("\\\\", "\\").replace("\\/", "/"))
            if "def " in code or "import " in code or "class " in code:
                extracted = code
        if extracted:
            pyfile.write_text(extracted, encoding="utf-8")
            repaired_files.append(str(pyfile.relative_to(p)))
    if repaired_files:
        return {"repaired": True, "files": repaired_files,
                "message": f"🔧 Αυτόματη επιδιόρθωση: εξήχθη Python κώδικας από JSON blob σε {repaired_files}"}
    return {"repaired": False, "files": [], "message": ""}


def _launch_app_proc(run_cmd: str, app_name: str) -> dict:
    """Launch a subprocess and collect first 1.5s of output. Returns info dict."""
    import subprocess as _sp, sys as _sys, threading, time
    parts = run_cmd.replace("python ", f"{_sys.executable} ").split()
    proc = _sp.Popen(parts, stdout=_sp.PIPE, stderr=_sp.STDOUT,
                     cwd=str(__import__("pathlib").Path(".").resolve()),
                     text=True, bufsize=1)
    info = {"proc": proc, "pid": proc.pid, "cmd": run_cmd, "log": ""}
    _running_apps[app_name] = info
    lines = []
    def _reader():
        for line in proc.stdout:
            lines.append(line)
            _running_apps.get(app_name, {})["log"] = (
                _running_apps.get(app_name, {}).get("log", "") + line
            )
            if len(lines) > 200:
                break
    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    time.sleep(1.5)
    return {"proc": proc, "pid": proc.pid, "lines": lines}


@app.route("/remote/app-builder/run-app", methods=["POST"])
def app_builder_run_app_route():
    """Start an app from apps/<app_name>/ with autonomous self-repair on failure."""
    from pathlib import Path as _P
    global _running_apps

    data = request.get_json(silent=True) or {}
    app_name = data.get("app", "").strip()
    run_cmd = data.get("run_command", "").strip()
    if not app_name:
        return jsonify({"ok": False, "error": "app name required"})

    # Kill previous instance if running
    if app_name in _running_apps:
        try:
            _running_apps[app_name]["proc"].terminate()
        except Exception:
            pass
        del _running_apps[app_name]

    app_dir = _P("apps") / app_name
    if not app_dir.exists():
        return jsonify({"ok": False, "error": f"apps/{app_name} not found"})

    if not run_cmd:
        run_cmd = _detect_run_command(app_dir)

    repair_msg = ""

    # ── STEP 1: Pre-flight — scan for JSON blob files before running ──────────
    repair = _try_autorepair_app(app_dir)
    if repair["repaired"]:
        repair_msg = repair["message"]

    # ── STEP 2: First launch attempt ──────────────────────────────────────────
    try:
        r1 = _launch_app_proc(run_cmd, app_name)
        proc, lines = r1["proc"], r1["lines"]
        output_text = "".join(lines[-40:])

        # ── STEP 3: Detect failure + auto-repair ──────────────────────────────
        failed = proc.poll() is not None
        has_syntax_error = "SyntaxError" in output_text or "invalid syntax" in output_text
        has_json_blob_error = "```json" in output_text or ("line 1" in output_text and "SyntaxError" in output_text)

        if failed and (has_syntax_error or has_json_blob_error):
            # Try repair even if pre-flight didn't catch it
            repair2 = _try_autorepair_app(app_dir)
            if repair2["repaired"]:
                repair_msg += ("\n" if repair_msg else "") + repair2["message"]
                # Re-launch after repair
                del _running_apps[app_name]
                r2 = _launch_app_proc(run_cmd, app_name)
                proc, lines = r2["proc"], r2["lines"]
                output_text = "".join(lines[-40:])
                failed = proc.poll() is not None
                if not failed:
                    output_text = (repair_msg + "\n✅ Επανεκκίνηση μετά από επιδιόρθωση!\n\n") + output_text
                else:
                    output_text = (repair_msg + "\n⚠️ Επιδιορθώθηκε αλλά εξακολουθεί να αποτυγχάνει:\n\n") + output_text
            else:
                output_text = "❌ SyntaxError — δεν ήταν δυνατή η αυτόματη επιδιόρθωση.\n" + output_text
        elif repair_msg:
            output_text = repair_msg + "\n\n" + output_text

        return jsonify({
            "ok": True,
            "pid": proc.pid,
            "app": app_name,
            "cmd": run_cmd,
            "running": proc.poll() is None,
            "output": output_text,
            "repaired": bool(repair_msg),
            "repair_msg": repair_msg,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/remote/app-builder/app-log")
def app_builder_app_log_route():
    """Return recent stdout/stderr of a running app."""
    global _running_apps
    app_name = request.args.get("app", "").strip()
    info = _running_apps.get(app_name)
    if not info:
        return jsonify({"ok": False, "running": False, "log": "", "error": "not running"})
    running = info["proc"].poll() is None
    return jsonify({"ok": True, "running": running, "pid": info["pid"],
                    "cmd": info["cmd"], "log": info["log"][-3000:]})


@app.route("/remote/app-builder/stop-app", methods=["POST"])
def app_builder_stop_app_route():
    """Terminate a running app subprocess."""
    global _running_apps
    data = request.get_json(silent=True) or {}
    app_name = data.get("app", "").strip()
    if app_name not in _running_apps:
        return jsonify({"ok": False, "error": "not running"})
    try:
        _running_apps[app_name]["proc"].terminate()
        del _running_apps[app_name]
        return jsonify({"ok": True, "stopped": app_name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/remote/app-builder/download/<app_name>")
def app_builder_download_route(app_name):
    """Download the entire app folder as a ZIP file."""
    import zipfile, io
    from pathlib import Path as _P
    from flask import send_file
    app_dir = _P("apps") / app_name
    if not app_dir.exists():
        return jsonify({"ok": False, "error": "not found"}), 404
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(app_dir.rglob("*")):
            if f.is_file():
                zf.write(f, arcname=str(f.relative_to(_P("apps"))))
    buf.seek(0)
    return send_file(buf, mimetype="application/zip",
                     as_attachment=True, download_name=f"{app_name}.zip")



@app.route("/remote/document-chat/ask", methods=["POST"])
def remote_document_chat_ask_route():
    data = request.get_json(silent=True) or {}
    msg = (
        data.get("message")
        or data.get("prompt")
        or data.get("text")
        or data.get("command")
        or ""
    )
    result = document_chat_answer(str(msg))
    formatted = format_document_answer(str(msg))
    return jsonify({
        "ok": True,
        "source": "document_chat_bridge",
        "mode": "document_recall",
        "used_documents": result.get("used_documents", False),
        "answer": formatted or result.get("answer"),
        "response": formatted or result.get("answer"),
        "text": formatted or result.get("answer"),
        "sources": result.get("sources", []),
        "raw": result,
    })




@app.route("/remote/document/upload", methods=["POST"])
def remote_document_upload_route():
    try:
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "missing_file"}), 400

        f = request.files["file"]
        note = request.form.get("note", "uploaded_from_ui")
        filename = f.filename or "upload.bin"

        upload_dir = Path("data/document_uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe = "".join(ch if ch.isalnum() or ch in ".-_ " else "_" for ch in filename).strip() or "upload.bin"
        target = upload_dir / safe

        i = 1
        while target.exists():
            target = upload_dir / f"{i}_{safe}"
            i += 1

        f.save(str(target))

        result = process_uploaded_file(target, original_name=filename, note=note)

        answer = result.get("answer", "Το αρχείο ανέβηκε.")
        return jsonify({
            "ok": bool(result.get("ok")),
            "source": "upload_processing_engine",
            "mode": "document_upload",
            "answer": answer,
            "response": answer,
            "text": answer,
            "human_answer": answer,
            "result": result,
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "source": "upload_processing_engine",
            "mode": "document_upload_error",
            "error": repr(e),
            "answer": "Το upload απέτυχε.",
            "response": "Το upload απέτυχε.",
            "text": "Το upload απέτυχε.",
            "human_answer": "Το upload απέτυχε.",
        }), 500


@app.route("/remote/document/upload-status", methods=["GET"])
def remote_document_upload_status_route():
    return jsonify(upload_status())




@app.route("/remote/conversations", methods=["GET"])
def remote_conversations_list_route():
    return jsonify(list_conversations())


@app.route("/remote/conversations/<conversation_id>", methods=["GET"])
def remote_conversation_get_route(conversation_id):
    return jsonify(get_conversation(conversation_id))


@app.route("/remote/conversations/<conversation_id>/rename", methods=["POST"])
def remote_conversation_rename_route(conversation_id):
    data = request.get_json(silent=True) or {}
    return jsonify(rename_conversation(conversation_id, data.get("title", "")))


@app.route("/remote/conversations/<conversation_id>", methods=["DELETE"])
def remote_conversation_delete_route(conversation_id):
    return jsonify(delete_conversation(conversation_id))




@app.route("/remote/conversations/search", methods=["POST"])
def remote_conversations_search_route():
    data = request.get_json(silent=True) or {}
    return jsonify(search_conversations(data.get("query", ""), int(data.get("limit", 8))))


@app.route("/remote/conversations/<conversation_id>/auto-title", methods=["POST"])
def remote_conversation_auto_title_route(conversation_id):
    return jsonify(generate_conversation_title(conversation_id))


@app.route("/remote/conversations/auto-title", methods=["POST"])
def remote_conversations_auto_title_route():
    data = request.get_json(silent=True) or {}
    return jsonify(auto_title_recent_conversations(int(data.get("limit", 20))))




@app.route("/remote/knowledge/status", methods=["GET"])
def remote_knowledge_status_route():
    return jsonify(knowledge_memory_status())


@app.route("/remote/knowledge/search", methods=["POST"])
def remote_knowledge_search_route():
    data = request.get_json(silent=True) or {}
    return jsonify(search_knowledge(data.get("query", ""), int(data.get("limit", 5))))


@app.route("/remote/knowledge/remember", methods=["POST"])
def remote_knowledge_remember_route():
    data = request.get_json(silent=True) or {}
    return jsonify(remember_knowledge(
        question=data.get("question", ""),
        answer=data.get("answer", ""),
        sources=data.get("sources", []),
        kind=data.get("kind", "manual"),
        confidence=data.get("confidence", "medium"),
        tags=data.get("tags", []),
    ))


@app.route("/remote/code-lessons/search", methods=["POST"])
def remote_code_lessons_search_route():
    data = request.get_json(silent=True) or {}
    return jsonify(search_code_lessons(data.get("query", ""), int(data.get("limit", 8))))




@app.route("/remote/quality-gate/run", methods=["POST"])
def remote_quality_gate_run_route():
    data = request.get_json(silent=True) or {}
    return jsonify(quality_gate(data.get("files") or None, data.get("label", "remote")))


@app.route("/remote/error-learning/status", methods=["GET"])
def remote_error_learning_status_route():
    return jsonify(error_learning_status())


@app.route("/remote/error-learning/search-errors", methods=["POST"])
def remote_error_learning_search_errors_route():
    data = request.get_json(silent=True) or {}
    return jsonify(search_errors(data.get("query", ""), int(data.get("limit", 8))))


@app.route("/remote/error-learning/search-solutions", methods=["POST"])
def remote_error_learning_search_solutions_route():
    data = request.get_json(silent=True) or {}
    return jsonify(search_solutions(data.get("query", ""), int(data.get("limit", 8))))


# ─────────────────────────────────────────────
# ΠΕΔΙΟ & ΧΑΡΤΗΣ — Field Diary / Vision AI
# ─────────────────────────────────────────────

FIELD_VISION_PROMPTS = {
    "signs": (
        "Είσαι ειδικός σε παραδοσιακά σημάδια θησαυρού και κρυφής επικοινωνίας στην Ελλάδα. "
        "Αναλύει αυτή την εικόνα και εντόπισε: "
        "1) Συμβολισμοί — βυζαντινά, οθωμανικά, ή ΕΛΑΣ/ΕΑΜ σημάδια "
        "2) Κατεύθυνση — βέλη, γραμμές, σχήματα που δείχνουν κατεύθυνση ή απόσταση "
        "3) Τύπος σημαδιού — FRP, IRP, cache marker, ή αναγνωριστικό "
        "4) Τεχνική — σκαλιστό, βαμμένο, φυσικό σχήμα "
        "5) Ερμηνεία — τι πιθανολογεί να σημαίνει στο πλαίσιο κρυμμένου θησαυρού "
        "Να είσαι συγκεκριμένος και πρακτικός."
    ),
    "terrain": (
        "Είσαι ειδικός σε ανάλυση εδάφους και γεωμορφολογία. "
        "Εξέτασε αυτή την εικόνα τοπίου/εδάφους και αναφέρου: "
        "1) Ανωμαλίες εδάφους — ασυνήθιστα υψώματα, βυθίσματα, αλλαγές χρώματος χώματος "
        "2) Βλάστηση — ανώμαλη ανάπτυξη που μπορεί να υποδηλώνει διατάραξη εδάφους "
        "3) Τεχνητά χαρακτηριστικά — παλιά τοιχοδομία, κατεδαφισμένα κτίσματα, μονοπάτια "
        "4) Υδρολογία — κανάλια, φρέατα, πηγές "
        "5) Πιθανές θέσεις ενδιαφέροντος για ανασκαφή"
    ),
    "map": (
        "Είσαι ειδικός αναγνώστης παλαιών χαρτών και χαρτογραφίας. "
        "Αναλύσε αυτόν τον χάρτη: "
        "1) Εποχή και στυλ χαρτογράφησης "
        "2) Τοπωνύμια — αναγνώρισε ονόματα τοποθεσιών "
        "3) Σύμβολα — εκκλησίες, πηγές, κτήρια, μονοπάτια "
        "4) Σημεία αναφοράς IRP/FRP αν υπάρχουν "
        "5) Σχέση με σύγχρονη γεωγραφία Μεσσηνίας"
    ),
    "rock": (
        "Είσαι ειδικός σε επιγραφές και χαράγματα σε πέτρα. "
        "Εξέτασε αυτή την εικόνα και αναφέρου: "
        "1) Τύπος χαράγματος — σύμβολα, γράμματα, αριθμοί, σχήματα "
        "2) Εποχή — πότε πιθανόν έγινε (βυζαντινό, οθωμανικό, νεότερο) "
        "3) Γλώσσα/αλφάβητο αν αναγνωρίζεται "
        "4) Σημασία στο πλαίσιο σημαδιών θησαυρού "
        "5) Προτεινόμενες επόμενες ενέργειες έρευνας"
    ),
    "artifact": (
        "Είσαι ειδικός σε αρχαιολογικά και ιστορικά ευρήματα Μεσσηνίας. "
        "Αναγνώρισε αυτό το αντικείμενο: "
        "1) Τύπος — νόμισμα, κοσμήματα, σκεύος, όπλο, άλλο "
        "2) Εποχή και προέλευση "
        "3) Υλικό — μέταλλο, κεραμικό, πέτρα "
        "4) Κατάσταση διατήρησης "
        "5) Ιστορική και αρχαιολογική σημασία"
    ),
    "general": (
        "Είσαι ο ΝΟΥΣ, ειδικός σύμβουλος ηλεκτρονικής ανίχνευσης και θησαυροθηρίας στη Μεσσηνία. "
        "Αναλύσε αυτή την εικόνα από κάθε πιθανή οπτική γωνία: "
        "σημάδια, σύμβολα, τοπογραφία, ανωμαλίες εδάφους, ιστορικά στοιχεία. "
        "Δώσε πρακτικές συστάσεις για την έρευνα."
    ),
}


@app.route("/field/analyze-image", methods=["POST"])
def field_analyze_image_route():
    try:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get("image_b64", "")
        mime = data.get("mime", "image/jpeg")
        analysis_type = data.get("analysis_type", "general")
        extra_context = data.get("context", "").strip()

        if not image_b64:
            return jsonify({"ok": False, "error": "Δεν δόθηκε εικόνα."})

        system_prompt = FIELD_VISION_PROMPTS.get(analysis_type, FIELD_VISION_PROMPTS["general"])
        prompt = "Αναλύσε αυτή την εικόνα."
        if extra_context:
            prompt += f"\n\nΠλαίσιο από χρήστη: {extra_context}"

        result = ask_with_image(prompt, image_b64, mime, system=system_prompt)
        if result.get("success") or result.get("ok"):
            return jsonify({
                "ok": True,
                "analysis": result.get("response", ""),
                "model": result.get("model", ""),
            })
        else:
            return jsonify({"ok": False, "error": result.get("error", "Σφάλμα ανάλυσης")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/field/add", methods=["POST"])
def field_add_route():
    try:
        data = request.get_json(silent=True) or {}
        title = data.get("title", "").strip()
        if not title:
            return jsonify({"ok": False, "error": "Ο τίτλος είναι υποχρεωτικός."})
        result = add_entry(
            title=title,
            note=data.get("note", ""),
            lat=data.get("lat"),
            lon=data.get("lon"),
            entry_type=data.get("entry_type", "note"),
            tags=data.get("tags") or [],
            analysis=data.get("analysis", ""),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/field/list", methods=["GET"])
def field_list_route():
    try:
        limit = int(request.args.get("limit", 80))
        entry_type = request.args.get("type", None) or None
        entries = list_entries(limit=limit, entry_type=entry_type)
        return jsonify({"ok": True, "entries": entries, "count": len(entries)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "entries": []})


@app.route("/field/delete", methods=["POST"])
def field_delete_route():
    try:
        data = request.get_json(silent=True) or {}
        entry_id = data.get("id", "")
        if not entry_id:
            return jsonify({"ok": False, "error": "Δεν δόθηκε id."})
        return jsonify(delete_entry(entry_id))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/field/markers", methods=["GET"])
def field_markers_route():
    try:
        markers = get_map_markers()
        return jsonify({"ok": True, "markers": markers, "count": len(markers)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "markers": []})


@app.route("/larmor/history", methods=["GET"])
def larmor_history_load():
    """Load persisted Larmor chat history from disk."""
    try:
        import json as _json
        path = os.path.join("data", "larmor_chat_history.json")
        if not os.path.exists(path):
            return jsonify({"ok": True, "history": [], "count": 0})
        with open(path, "r", encoding="utf-8") as f:
            history = _json.load(f)
        if not isinstance(history, list):
            history = []
        return jsonify({"ok": True, "history": history, "count": len(history)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "history": []})


@app.route("/larmor/history", methods=["POST"])
def larmor_history_save():
    """Persist Larmor chat history to disk."""
    try:
        import json as _json
        data = request.get_json(silent=True) or {}
        history = data.get("history", [])
        if not isinstance(history, list):
            return jsonify({"ok": False, "error": "history must be an array"})
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "larmor_chat_history.json")
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(history, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True, "saved": len(history)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ─── DAILY BRIEF ──────────────────────────────────────────────────────────────
@app.route("/remote/daily-brief", methods=["GET"])
def remote_daily_brief_route():
    try:
        from executor.daily_brief import daily_brief
        return jsonify(daily_brief())
    except Exception as e:
        return jsonify({"error": str(e)})


# ─── PROJECT HEALTH SNAPSHOT ──────────────────────────────────────────────────
@app.route("/remote/project-health", methods=["GET"])
def remote_project_health_route():
    try:
        from executor.project_health_snapshot import run_project_health_snapshot
        return jsonify(run_project_health_snapshot())
    except Exception as e:
        return jsonify({"error": str(e)})


# ─── GUERRILLA SIGNS KNOWLEDGE SEARCH ────────────────────────────────────────
@app.route("/field/signs/search", methods=["POST"])
def field_signs_search_route():
    try:
        from executor.guerrilla_signs_knowledge import get_guerrilla_signs_chunks
        data = request.get_json(silent=True) or {}
        query = (data.get("query") or "").lower().strip()
        chunks = get_guerrilla_signs_chunks()
        if not query:
            return jsonify({"ok": True, "results": chunks, "total": len(chunks)})
        results = []
        for c in chunks:
            hay = (c.get("question", "") + " " + c.get("answer", "") + " " + " ".join(c.get("tags", []))).lower()
            if query in hay:
                results.append(c)
        return jsonify({"ok": True, "results": results, "total": len(results), "query": query})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ─── RUNTIME METRICS ──────────────────────────────────────────────────────────
@app.route("/remote/runtime-metrics", methods=["GET"])
def remote_runtime_metrics_route():
    try:
        from executor.runtime_metrics import collect_metrics
        return jsonify(collect_metrics())
    except Exception as e:
        return jsonify({"error": str(e)})


# ── NOUS Drive: auto-think background thread ──────────────────────────────────
def _nous_drive_background():
    """Run nous_drive.think() every 15 minutes in background."""
    import time as _t
    _t.sleep(30)  # wait for app to finish starting
    while True:
        try:
            nous_drive_think(force=False)
        except Exception:
            pass
        _t.sleep(900)  # 15 minutes

import threading as _threading
_drive_thread = _threading.Thread(target=_nous_drive_background, daemon=True)
_drive_thread.start()

try:
    start_scheduler()
except Exception:
    pass

if __name__ == "__main__":
    print("🧠 NUS AI OS LEVEL 22 RUNNING")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
