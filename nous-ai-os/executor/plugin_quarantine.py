import re
import shutil
from pathlib import Path

PLUGIN_DIR = Path("executor/plugins")
QUARANTINE_DIR = Path("executor/quarantine")
_PLUGIN_NAME = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")


def quarantine(name):
    if not isinstance(name, str) or not _PLUGIN_NAME.fullmatch(name):
        return {"success": False, "error": "invalid_plugin_name"}

    plugin_root = PLUGIN_DIR.resolve()
    source = (plugin_root / f"{name}.py").resolve()
    if source.parent != plugin_root or not source.is_file():
        return {"success": False, "error": "plugin_not_found"}

    quarantine_root = QUARANTINE_DIR.resolve()
    quarantine_root.mkdir(parents=True, exist_ok=True)
    destination = (quarantine_root / f"{name}.py").resolve()
    if destination.parent != quarantine_root:
        return {"success": False, "error": "invalid_quarantine_path"}

    shutil.move(str(source), str(destination))
    return {"success": True, "quarantined": name, "path": str(destination)}
