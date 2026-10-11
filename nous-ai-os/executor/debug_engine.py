import ast


def run_code(code):
    """Inspect source syntax and declared names without executing the source."""
    try:
        tree = ast.parse(code)
        defined_names = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        return {
            "output": {
                "validation": "static_only",
                "defined_names": defined_names,
            },
            "execution_skipped": True,
        }
    except (SyntaxError, ValueError, TypeError) as exc:
        return {"error": str(exc)}
