import ast


def test_plugin(code: str):
    """Statically validate plugin source without running untrusted Python."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, TypeError) as exc:
        return {"success": False, "error": str(exc)}

    has_run = any(
        isinstance(node, ast.FunctionDef) and node.name == "run"
        for node in tree.body
    )
    if not has_run:
        return {"success": False, "error": "Missing top-level run() function"}

    return {
        "success": True,
        "execution_skipped": True,
        "result": {
            "validation": "static_only",
            "run_function_found": True,
        },
    }
