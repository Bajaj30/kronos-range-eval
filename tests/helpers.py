def assert_counts(actual: dict, expected: dict) -> None:
    """Exact match on every key. A key missing from either side is a failure, not a pass (playbook 6.7)."""
    missing = set(actual) ^ set(expected)
    assert not missing, f"keys present on only one side: {sorted(missing)}"
    wrong = {k: (actual[k], expected[k]) for k in expected if actual[k] != expected[k]}
    assert not wrong, f"(actual, expected) differ: {wrong}"
