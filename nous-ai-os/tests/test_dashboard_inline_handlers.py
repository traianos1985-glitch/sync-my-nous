import re
from pathlib import Path

from executor import nous_ui


_JS_BUILTINS = {
    "if",
    "for",
    "while",
    "function",
    "alert",
    "confirm",
    "prompt",
    "fetch",
    "setTimeout",
    "setInterval",
    "localStorage",
    "document",
    "Math",
    "String",
    "JSON",
    "Number",
    "parseInt",
    "parseFloat",
    "event",
}


def test_dashboard_inline_click_handlers_have_function_definitions():
    source_path = Path(nous_ui.__file__)
    source = source_path.read_text(encoding="utf-8")
    defined = set(
        re.findall(r"\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", source)
    )
    expressions = re.findall(r"onclick\s*=\s*([\"'])(.*?)\1", source, flags=re.IGNORECASE | re.DOTALL)

    referenced = set()
    for _, expression in expressions:
        referenced.update(
            name
            for name in re.findall(r"(?:^|[;{}\s])([A-Za-z_$][\w$]*)\s*\(", expression)
            if name not in _JS_BUILTINS
        )

    missing = sorted(referenced - defined)
    assert not missing, f"Dashboard click handlers without function definitions: {missing}"
