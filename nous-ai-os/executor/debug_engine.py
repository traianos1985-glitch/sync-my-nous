import ast


def run_code(code):
    """Inspect source syntax and declared names without executing the source."""
    try:
        tree = ast.parse(code)
        defined_names = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_names.append(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                defined_names.extend(
                    target.id for target in targets if isinstance(target, ast.Name)
                )
        return {
            "output": {
                "validation": "static_only",
                "defined_names": defined_names,
            },
            "execution_skipped": True,
        }
    except (SyntaxError, ValueError, TypeError) as exc:
        return {"error": str(exc)}
