"""Ensure run_*.py CLI entry points still target existing executor APIs."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "executor"


def _module_path(module_name):
    relative = Path(*module_name.split("."))
    module_file = EXECUTOR.parent / relative.with_suffix(".py")
    package_file = EXECUTOR.parent / relative / "__init__.py"
    if module_file.is_file():
        return module_file
    if package_file.is_file():
        return package_file
    return None


def _top_level_symbols(source_path):
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    symbols = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.Import):
            symbols.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            symbols.update(alias.asname or alias.name for alias in node.names if alias.name != "*")
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    symbols.update(item.id for item in target.elts if isinstance(item, ast.Name))
    return symbols


def test_every_run_script_imports_existing_executor_modules_and_symbols():
    scripts = sorted(ROOT.glob("run_*.py"))
    assert len(scripts) >= 25, "Expected the established CLI entry-point scripts to remain present"

    problems = []
    symbol_cache = {}
    for script in scripts:
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except (OSError, SyntaxError, UnicodeError) as exc:
            problems.append(f"{script.name}: cannot parse ({exc})")
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module or not node.module.startswith("executor."):
                continue
            target_path = _module_path(node.module)
            if target_path is None:
                problems.append(f"{script.name}: missing module {node.module}")
                continue
            if target_path not in symbol_cache:
                try:
                    symbol_cache[target_path] = _top_level_symbols(target_path)
                except (OSError, SyntaxError, UnicodeError) as exc:
                    problems.append(f"{script.name}: cannot parse {node.module} ({exc})")
                    continue
            for imported in node.names:
                if imported.name == "*":
                    continue
                if imported.name not in symbol_cache[target_path]:
                    problems.append(
                        f"{script.name}: {node.module} does not expose {imported.name}"
                    )

    assert not problems, "Broken CLI entry-point imports:\n" + "\n".join(sorted(problems))
