"""Which browser origins may call the NOUS API cross-site.

executor/router.py checks the request Origin before it answers any API call. The
module cannot be imported in a test (it boots the whole runtime and refuses to
start without the master token), so the allowlist helper is lifted out of the
source with `ast` and exercised directly here.
"""

import ast
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "nous-ai-os" / "executor" / "router.py"

WANTED = {"ALLOWED_ORIGINS", "ALLOWED_ORIGIN_SUFFIXES", "_origin_allowed"}


def _allowlist_namespace():
    """Run just the Origin rules from router.py, without importing the runtime."""
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"), filename=str(ROUTER))
    picked = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in WANTED:
            picked.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in WANTED for target in node.targets
        ):
            picked.append(node)

    found = set()
    for node in picked:
        if isinstance(node, ast.FunctionDef):
            found.add(node.name)
        else:
            found.update(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
    missing = WANTED - found
    assert not missing, f"router.py no longer defines {sorted(missing)}"

    module = ast.Module(body=picked, type_ignores=[])
    namespace = {"os": os, "urlsplit": urlsplit}
    exec(compile(ast.fix_missing_locations(module), str(ROUTER), "exec"), namespace)
    return namespace


ALLOWED = [
    # Lovable previews and published apps, the address the dashboard is served from.
    "https://id-preview--1fa033ea-3834-40b6-aaeb-011deabdf812.lovable.app",
    "https://nous-ai-os-web.lovable.app",
    "https://id-preview--1fa033ea.lovableproject.com",
    "https://nous-dashboard.lovableproject.com",
    "https://nous-ai-os.lovable.dev",
    "https://lovable.dev",
    # Deployed dashboard, GitHub Pages and local development stay listed exactly.
    "https://sync-my-nous.vercel.app",
    "https://traianos1985-glitch.github.io",
    "http://localhost:5173",
    "http://localhost:8080",
]

DENIED = [
    "https://evil-lovable.app",  # look-alike: no subdomain boundary
    "https://lovable.app.evil.com",
    "https://notlovable.dev",
    "https://x.lovableproject.com.evil.com",
    "http://insecure.lovable.app",  # previews are always served over https
    "https://attacker.example",
    "",
]


def test_all_three_lovable_domains_are_in_the_allowlist():
    suffixes = _allowlist_namespace()["ALLOWED_ORIGIN_SUFFIXES"]
    assert {".lovable.app", ".lovableproject.com", ".lovable.dev"} <= set(suffixes)


def test_lovable_preview_and_published_origins_are_accepted():
    check = _allowlist_namespace()["_origin_allowed"]
    assert [origin for origin in ALLOWED if not check(origin)] == []


def test_lookalike_and_plain_http_origins_are_rejected():
    check = _allowlist_namespace()["_origin_allowed"]
    assert [origin for origin in DENIED if check(origin)] == []


def test_missing_origin_is_rejected():
    check = _allowlist_namespace()["_origin_allowed"]
    assert check(None) is False
