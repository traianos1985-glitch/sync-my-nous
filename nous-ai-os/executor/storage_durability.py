"""Report whether NOUS state survives restarts on this host (no paths or secrets exposed)."""
import os

_TRUTHY = {"1", "true", "yes", "on"}


def storage_report(data_dir="data"):
    """Classify the data directory as persistent or ephemeral.

    Render Free has no disk: every restart or wake-up resets files under the app.
    A Render disk is a mount point at the data directory; operators may also
    declare durable storage explicitly with NOUS_PERSISTENT_STORAGE=1.
    """
    path = os.path.abspath(data_dir)
    on_render = bool(os.environ.get("RENDER", "").strip() or os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip())
    mounted = os.path.isdir(path) and os.path.ismount(path)
    declared = os.environ.get("NOUS_PERSISTENT_STORAGE", "").strip().lower() in _TRUTHY
    if mounted:
        mode = "persistent_disk"
    elif declared:
        mode = "declared_persistent"
    elif on_render:
        mode = "ephemeral"
    else:
        mode = "local_disk"
    durable = mode != "ephemeral"
    autonomy_default = os.environ.get("NOUS_AUTONOMY_ENABLED_DEFAULT", "").strip().lower() in _TRUTHY
    return {
        "ok": True,
        "mode": mode,
        "durable": durable,
        "host": "render" if on_render else "other",
        "autonomy_enabled_by_default": autonomy_default,
        "warning": None if durable else (
            "Ο δίσκος αυτού του server δεν είναι μόνιμος: σε κάθε restart ή αφύπνιση χάνονται "
            "missions, μνήμη, ρυθμίσεις αυτονομίας και logs."
        ),
    }
