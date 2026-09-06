import os

from executor.snapshots import create_snapshot, rollback
from executor.plugin_loader import load_plugins

def analyze_system():

    plugins = load_plugins()

    issues = []

    if len(plugins) == 0:
        issues.append("no_plugins_loaded")

    return issues


def improve():

    snapshot = create_snapshot()
    issues = analyze_system()

    if "no_plugins_loaded" in issues:
        return {
            "action": "create_default_plugin",
            "snapshot": snapshot
        }

    return {
        "status": "healthy",
        "snapshot": snapshot
    }


def auto_heal():
    try:
        return improve()
    except Exception as e:
        # HARD SAFETY: rollback automatically
        snaps = list(os.listdir("executor/snapshots"))
        if snaps:
            return rollback(sorted(snaps)[-1])
        return {"fatal": str(e)}
