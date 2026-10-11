"""Backward-compatible wrapper for the guarded plugin writer."""
from executor import plugin_builder


def create_plugin(name, code):
    """Create a plugin through the same validation and exclusive-write path as NOUS."""
    result = plugin_builder.create_plugin(name, code)
    if not result.get("success"):
        return result

    # Preserve the legacy result keys for any older callers.
    return {
        "created": result["plugin"],
        "path": result["path"],
        "success": True,
    }
