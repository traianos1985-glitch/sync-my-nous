"""Keep every advertised catalog tool connected to a run_tool dispatch branch."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "executor" / "tool_catalog.py"
TOOLS_PATH = ROOT / "executor" / "tools.py"

# The user-facing catalog name differs from the runtime intent for this alias.
CATALOG_ACTION_ALIASES = {"time": "current_time"}


def _catalog_names():
    tree = ast.parse(CATALOG_PATH.read_text(encoding="utf-8"))
    names = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "TOOLS" for target in targets):
            continue
        value = node.value
        if not isinstance(value, (ast.Tuple, ast.List)):
            raise AssertionError("TOOL catalog must be a literal tuple or list")
        for item in value.elts:
            if not isinstance(item, ast.Dict):
                continue
            for key, entry_value in zip(item.keys, item.values):
                if isinstance(key, ast.Constant) and key.value == "name":
                    if not isinstance(entry_value, ast.Constant) or not isinstance(entry_value.value, str):
                        raise AssertionError("Catalog tool names must be literal strings")
                    names.append(entry_value.value)
                    break
    return names


def _run_tool_dispatch_actions():
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    run_tool = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "run_tool"
        ),
        None,
    )
    assert run_tool is not None, "executor.tools.run_tool is missing"

    actions = set()
    for node in ast.walk(run_tool):
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Name):
            continue
        if node.left.id != "action":
            continue
        for operator, comparator in zip(node.ops, node.comparators):
            if isinstance(operator, ast.Eq) and isinstance(comparator, ast.Constant):
                if isinstance(comparator.value, str):
                    actions.add(comparator.value)
            elif isinstance(operator, ast.In) and isinstance(comparator, (ast.Set, ast.Tuple, ast.List)):
                actions.update(
                    item.value
                    for item in comparator.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
    return actions


def test_catalog_names_are_unique_and_dispatchable():
    names = _catalog_names()
    assert names, "Tool catalog is empty"
    assert len(names) == len(set(names)), "Duplicate tool names in tool catalog"

    dispatch_actions = _run_tool_dispatch_actions()
    missing = sorted(
        name
        for name in names
        if CATALOG_ACTION_ALIASES.get(name, name) not in dispatch_actions
    )
    assert not missing, (
        "Catalog tools without a run_tool dispatch branch: " + ", ".join(missing)
    )

def test_tool_library_routes_have_one_canonical_registration_and_allowlist():
    root = Path(__file__).resolve().parents[1]
    router_source = (root / "executor" / "router.py").read_text(encoding="utf-8")
    dashboard_source = (root / "executor" / "dashboard_api.py").read_text(encoding="utf-8")

    assert '@app.route("/api/tools/catalog")' not in router_source
    assert '@app.route("/api/tools/run"' not in router_source
    assert dashboard_source.count('@dashboard_api_bp.get("/tools/catalog")') == 1
    assert dashboard_source.count('@dashboard_api_bp.post("/tools/run")') == 1
    assert "TOOL_LIBRARY_ALLOWED_ACTIONS" in dashboard_source
    assert "executable_from_tool_library" in dashboard_source
