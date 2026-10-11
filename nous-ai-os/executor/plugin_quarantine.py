import os
import re
from pathlib import Path

PLUGIN_DIR = Path("executor/plugins")
QUARANTINE_DIR = Path("executor/quarantine")
_PLUGIN_NAME = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")


def quarantine(name):
    if not isinstance(name, str) or not _PLUGIN_NAME.fullmatch(name):
        return {"success": False, "error": "invalid_plugin_name"}

    plugin_root = PLUGIN_DIR.resolve()
    candidate = plugin_root / f"{name}.py"
    if candidate.is_symlink() or not candidate.is_file():
        return {"success": False, "error": "plugin_not_found"}
    source = candidate.resolve()
    if source.parent != plugin_root:
        return {"success": False, "error": "invalid_plugin_path"}

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    quarantine_root = QUARANTINE_DIR.resolve()
    destination = quarantine_root / f"{name}.py"
    if destination.parent != quarantine_root:
        return {"success": False, "error": "invalid_quarantine_path"}
    if destination.exists() or destination.is_symlink():
        return {"success": False, "error": "quarantine_destination_exists"}

    # Atomic hard-link creation refuses an existing destination instead of
    # allowing a move to overwrite a previously quarantined artifact.
    try:
        os.link(source, destination, follow_symlinks=False)
        try:
            source.unlink()
        except OSError:
            destination.unlink(missing_ok=True)
            raise
    except FileExistsError:
        return {"success": False, "error": "quarantine_destination_exists"}
    except OSError as exc:
        return {"success": False, "error": f"quarantine_failed:{type(exc).__name__}"}

    return {"success": True, "quarantined": name, "path": str(destination)}
