import re

from executor.nous_ui import nous_dashboard_html


def test_every_static_navigation_tab_has_a_real_section():
    html = nous_dashboard_html()
    section_ids = set(re.findall(r'<section\b[^>]*\bid=["\']([^"\']+)["\']', html))
    nav_ids = set(re.findall(r'data-sec=["\']([^"\']+)["\']', html))
    nav_ids.discard("${id}")
    assert nav_ids <= section_ids
    assert section_ids <= nav_ids
    assert 'data-sec="toolbox"' in html
    assert 'id="toolbox"' in html
    assert 'getJson("/api/tools/catalog")' in html
    assert 'postJson("/api/tools/run"' in html


def test_inline_button_handlers_resolve_to_declared_functions_or_browser_methods():
    html = nous_dashboard_html()
    declared = set(re.findall(r'function\s+([A-Za-z_$][\w$]*)\s*\(', html))
    handlers = re.findall(r'onclick=["\']([^"\']+)["\']', html)
    called = set()
    for handler in handlers:
        called.update(re.findall(r'([A-Za-z_$][\w$]*)\s*\(', handler))
    browser_methods = {
        "removeItem", "stopPropagation", "getElementById", "stringify",
        "confirm", "alert", "prompt", "open", "close", "setTimeout",
        "clearTimeout", "setInterval", "clearInterval", "parseInt", "parseFloat",
        "encodeURIComponent", "decodeURIComponent",
    }
    missing = called - declared - browser_methods
    assert not missing, "Undeclared onclick handlers: " + ", ".join(sorted(missing))


def test_tool_library_does_not_claim_direct_execution_for_every_tool():
    html = nous_dashboard_html()
    assert "executable_from_tool_library === true" in html
    assert "δεν εκτελείται από αυτό το πάνελ" in html
    assert "loadToolbox" in html and "renderToolbox" in html
