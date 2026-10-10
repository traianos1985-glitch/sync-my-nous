from executor.agent_protocol import build_cycle_contract, digest_payload, validate_cycle_contract


def _cycle(action="act", allowed=True, specialist="builder"):
    guardian = {"role": "guardian", "status": "completed", "policy": {"allowed": allowed}}
    result = {
        "cycle_id": "cycle-test-001",
        "priority": {"action": action},
        "effective_action": "act",
        "guardian": guardian,
        "planner": {"role": "planner", "status": "completed", "decision": {"next": "test"}},
        "researcher": None,
        "builder": None,
        "reviewer": {"role": "reviewer", "status": "completed", "code_advice": {"ok": True}},
        "execution": {
            "status": "completed" if allowed else "blocked",
            "action": action,
            "reason": "test",
        },
    }
    if allowed and specialist == "builder":
        result["builder"] = {"role": "builder", "status": "completed", "code": {"healthy": True}}
    elif allowed and specialist == "researcher":
        result["researcher"] = {"role": "researcher", "status": "completed", "result": {"items": 1}}
    return result


def test_contract_records_hashes_and_explicit_integrity_scope():
    output = _cycle()
    contract = build_cycle_contract(output)
    assert contract["valid"] is True
    assert contract["roles"]["builder"]["sha256"] == digest_payload(output["builder"])
    assert contract["integrity_scope"] == "structural_consistency_not_factual_verification"
    assert validate_cycle_contract(contract, output)["ok"] is True


def test_contract_rejects_specialist_when_guardian_denies():
    output = _cycle(allowed=False)
    output["builder"] = {"role": "builder", "status": "completed"}
    contract = build_cycle_contract(output)
    assert contract["checks"]["guardian_gate_consistent"] is False
    assert contract["valid"] is False


def test_contract_rejects_failed_specialist_reported_as_completed():
    output = _cycle()
    output["builder"] = {"role": "builder", "status": "failed", "error": "boom"}
    output["execution"]["status"] = "completed"
    contract = build_cycle_contract(output)
    assert contract["checks"]["failed_specialist_is_reported"] is False
    assert contract["valid"] is False


def test_contract_detects_payload_mutation_after_creation():
    output = _cycle()
    contract = build_cycle_contract(output)
    output["builder"]["code"]["healthy"] = False
    validation = validate_cycle_contract(contract, output)
    assert validation["ok"] is False
    assert validation["digest_matches"] is False


def test_contract_handles_no_action_without_specialist():
    output = _cycle(action="idle", allowed=True)
    output["builder"] = None
    output["execution"]["status"] = "no_action"
    contract = build_cycle_contract(output)
    assert contract["valid"] is True


def test_contract_requires_failed_specialist_outcome_to_match_execution():
    output = _cycle()
    output["builder"] = {"role": "builder", "status": "failed", "error": "runtime"}
    output["execution"]["status"] = "failed"
    contract = build_cycle_contract(output)
    assert contract["valid"] is True
