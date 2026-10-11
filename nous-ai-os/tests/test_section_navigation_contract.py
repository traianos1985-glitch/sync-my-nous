"""Keep dashboard navigation and configured panels reachable from one another."""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NAV_PATH = ROOT / "src" / "components" / "nous" / "nav.ts"
CONFIG_PATH = ROOT / "src" / "components" / "nous" / "section-configs.ts"

# These panels have bespoke dashboard content rather than a SectionPanel config.
CUSTOM_SECTIONS = {"chat", "home", "documents", "control", "settings"}


def _navigation_ids():
    source = NAV_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"""\bid:\s*["']([^"']+)["']""", source))


def _configured_sections():
    source = CONFIG_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"(?m)^  ([a-z][a-z0-9-]*): \{", source))


def test_every_navigation_item_has_a_rendered_section():
    navigation_ids = _navigation_ids()
    configured_sections = _configured_sections()
    unsupported = sorted(navigation_ids - configured_sections - CUSTOM_SECTIONS)
    assert not unsupported, (
        "Navigation items without a configured or bespoke dashboard section: "
        + ", ".join(unsupported)
    )


def test_every_section_config_is_reachable_from_navigation():
    navigation_ids = _navigation_ids()
    configured_sections = _configured_sections()
    unreachable = sorted(configured_sections - navigation_ids)
    assert not unreachable, (
        "Section configs without a navigation entry (unreachable panels): "
        + ", ".join(unreachable)
    )
