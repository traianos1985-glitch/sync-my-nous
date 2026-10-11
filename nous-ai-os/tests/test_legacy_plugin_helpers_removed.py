"""Guard against reintroducing unused, unsafe legacy plugin helpers."""
import ast
from pathlib import Path


def test_legacy_plugin_helpers_have_no_remaining_python_references() -> None:
    root = Path(__file__).resolve().parents[1]
    test_file = Path(__file__).resolve()
    legacy_modules = {"plugin_creator", "plugin_loader", "plugin_sandbox"}
    references = []

    for path in root.rglob("*.py"):
        if path.resolve() == test_file:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in legacy_modules or alias.name in {
                        f"executor.{name}" for name in legacy_modules
                    }:
                        references.append(f"{path.relative_to(root)}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module in legacy_modules or node.module in {
                    f"executor.{name}" for name in legacy_modules
                }:
                    references.append(f"{path.relative_to(root)}:{node.lineno}")
                if node.module == "executor":
                    for alias in node.names:
                        if alias.name in legacy_modules:
                            references.append(f"{path.relative_to(root)}:{node.lineno}")

        for line_number, line in enumerate(source.splitlines(), start=1):
            if any(name in line for name in legacy_modules):
                references.append(f"{path.relative_to(root)}:{line_number}")

    assert not references, f"References to removed legacy plugin helpers: {sorted(set(references))}"
