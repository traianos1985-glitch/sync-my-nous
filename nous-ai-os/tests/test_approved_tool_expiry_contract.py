from pathlib import Path


def test_expired_approved_tool_actions_are_rejected_before_and_during_claim():
    route = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "routes"
        / "api.tools.execute.ts"
    )
    source = route.read_text(encoding="utf-8")

    expiry_guard = "gt(nousApprovals.expiresAt, new Date())"
    assert expiry_guard in source

    validation = source.split(
        "// Validate the approved action before claiming it.", maxsplit=1
    )[1].split("// Conditional update is the single-winner claim.", maxsplit=1)[0]
    claim = source.split(
        "// Conditional update is the single-winner claim.", maxsplit=1
    )[1].split("if (!approval)", maxsplit=1)[0]

    assert expiry_guard in validation
    assert expiry_guard in claim
