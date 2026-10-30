"""Deprecated interactive approval shim.

Web/server execution must use executor.operator_approval and its durable,
single-use approval records. This compatibility function deliberately fails
closed rather than prompting on stdin or silently approving an action.
"""


def ask_approval(action):
    """Reject legacy console approval; callers must migrate to operator_approval."""
    label = str(action).strip()[:128]
    raise RuntimeError(
        "interactive_approval_removed: use executor.operator_approval "
        f"for explicit approval of {label!r}"
    )
