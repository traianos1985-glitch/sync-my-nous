from executor.id_compat import find_by_id, new_runtime_id


def test_new_runtime_id_is_javascript_safe_and_unique():
    first = new_runtime_id()
    second = new_runtime_id([first])
    assert 0 < first <= 9_007_199_254_740_991
    assert 0 < second <= 9_007_199_254_740_991
    assert second != first


def test_find_by_id_prefers_exact_match():
    items = [{"id": 123, "name": "exact"}, {"id": 124, "name": "other"}]
    assert find_by_id(items, "123")["name"] == "exact"


def test_find_by_id_recovers_unique_legacy_nanosecond_id_after_js_rounding():
    legacy_id = 1_791_744_552_678_172_561
    rounded_id = int(float(legacy_id))
    items = [{"id": legacy_id, "name": "legacy"}]
    assert str(rounded_id) != str(legacy_id)
    assert find_by_id(items, rounded_id)["name"] == "legacy"


def test_find_by_id_rejects_ambiguous_legacy_numeric_match():
    first = 1_791_744_552_678_172_561
    second = 1_791_744_552_678_172_562
    items = [{"id": first}, {"id": second}]
    rounded_id = int(float(first))
    assert find_by_id(items, rounded_id) is None
