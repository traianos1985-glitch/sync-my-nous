from executor.agent_goal_policy import requires_code_generation


def test_code_generation_policy_matches_supported_english_terms():
    assert requires_code_generation("create a plugin")
    assert requires_code_generation("build a calculator")
    assert requires_code_generation("write code")


def test_code_generation_policy_matches_greek_code_stem_with_accents():
    assert requires_code_generation("γράψε κώδικα για την εφαρμογή")
    assert requires_code_generation("δημιουργία κωδικών")


def test_code_generation_policy_uses_word_boundaries():
    assert not requires_code_generation("decode this message")
    assert not requires_code_generation("research the weather")


def test_kernel_gate_uses_same_policy_as_agent_executor():
    from executor.kernel import _requires_approval
    tool = {"approval_required": "depends_on_action"}
    assert _requires_approval(tool, "agent_solve", "agent solve create a plugin")
    assert _requires_approval(tool, "agent_solve", "agent solve γράψε κώδικα")
    assert not _requires_approval(tool, "agent_solve", "agent solve research the weather")
    assert not _requires_approval(tool, "agent_solve", "agent solve decode this message")
