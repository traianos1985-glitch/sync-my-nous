from executor.intent import detect_intent
from executor.tools import run_tool
from executor.memory import save
from executor.hybrid_agent import run as hybrid_run
from executor.operator_approval import (
    claim_approved_approval,
    finish_approval,
    list_approvals,
    request_approval,
)
from executor.tool_catalog import get_tool



def _requires_approval(tool, action, command):
    if action == "cmd":
        # Shell commands have a dedicated command_execution approval workflow.
        return False
    required = tool.get("approval_required")
    if required is True:
        return True
    if required == "depends_on_action" and action == "agent_solve":
        # solve_goal invokes Code Forge for these goals, so its dynamic
        # approval must be applied before that nested code-generation path.
        lowered = str(command).lower()
        return any(term in lowered for term in ("plugin", "calculator", "κώδικ", "code"))
    return False


def _approval_result(action, approval_id=None):
    return {
        "ok": False,
        "approval_required": True,
        "action": action,
        "approval_id": str(approval_id) if approval_id is not None else None,
        "message": (
            "Η ενέργεια απαιτεί έγκριση διαχειριστή. Ενέκρινε το αίτημα στις "
            "Εγκρίσεις και επανάλαβε την ίδια εντολή μαζί με το approval_id."
        ),
    }


def _pending_approval(action, payload):
    for item in list_approvals(status="pending"):
        if item.get("action") == action and item.get("payload") == payload:
            return item
    return request_approval(
        action,
        payload,
        reason=f"Chat command '{payload['command']}' requires explicit approval",
    )


def handle(command, context=None):
    if context is None:
        context = {}

    context["command"] = command
    intent = detect_intent(command)

    save({
        "command": command,
        "intent": intent,
    })

    t = intent["type"]

    if t == "system":
        if intent["action"] == "status":
            return {
                "output": "ΝΟΥΣ AI OS RUNNING",
                "type": "system",
            }

        if intent["action"] == "evolve":
            return {
                "output": "LEVEL 27 CORE ACTIVE",
                "type": "system",
            }

    if t == "tool":
        action = intent.get("action")
        tool = get_tool(action)
        # Generic catalog approvals cover tools without a dedicated approval workflow.
        # The shell command tool has its own command_execution approval and must not
        # be wrapped in a second, incompatible approval claim.
        if tool and _requires_approval(tool, action, command):
            payload = {"command": command}
            approval_id = context.get("approval_id")

            if not approval_id:
                try:
                    approval = _pending_approval(action, payload)
                except Exception:
                    return {
                        "output": {
                            "ok": False,
                            "error": "approval_store_unavailable",
                            "approval_required": True,
                            "action": action,
                        },
                        "type": "tool",
                    }
                return {
                    "output": _approval_result(action, approval.get("id")),
                    "type": "tool",
                }

            claimed = claim_approved_approval(approval_id, action, payload)
            if not claimed:
                return {
                    "output": {
                        **_approval_result(action, approval_id),
                        "error": "valid_approval_required",
                    },
                    "type": "tool",
                }

            try:
                result = run_tool(intent, context)
            except Exception as exc:
                finish_approval(
                    approval_id,
                    "failed",
                    {"error": str(exc), "action": action},
                )
                return {
                    "output": {
                        "ok": False,
                        "error": "approved_tool_execution_failed",
                        "action": action,
                    },
                    "type": "tool",
                }

            finish_approval(
                approval_id,
                "completed",
                {"action": action, "result": result},
            )
            return {
                "output": result,
                "type": "tool",
                "approval_id": str(approval_id),
                "approval_status": "completed",
            }

        return {
            "output": run_tool(intent, context),
            "type": "tool",
        }

    try:
        result = hybrid_run(command, context)
        return {
            "output": result,
            "type": "reasoning",
        }
    except Exception as exc:
        return {
            "output": f"REASONING ERROR: {exc}",
            "type": "error",
        }
