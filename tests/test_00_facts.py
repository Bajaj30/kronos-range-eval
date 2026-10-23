import types

import pytest

from lib.facts import fact, render, write_step

CFG = types.SimpleNamespace(TICKERS={"NIFTY": "^NSEI"}, GAP_DAYS=5, lower_case_ignored=1)


def test_render_is_deterministic_and_shows_group(tmp_path):
    write_step(tmp_path, "00", "Test", "x.py", {"G1": "group one"}, [fact("rows", 2717, "G1", "rows seen")])
    a, b = render(CFG, tmp_path), render(CFG, tmp_path)
    assert a == b
    assert "| G1 | rows | 2717 | rows seen |" in a
    assert "| GAP_DAYS | 5 |" in a and "lower_case_ignored" not in a


def test_fact_with_undefined_group_is_refused(tmp_path):
    with pytest.raises(ValueError, match="undefined group"):
        write_step(tmp_path, "00", "T", "x.py", {"G1": "g"}, [fact("rows", 1, "G2", "d")])


def test_same_group_defined_differently_is_refused(tmp_path):
    write_step(tmp_path, "00", "T", "x.py", {"G1": "one meaning"}, [fact("a", 1, "G1", "d")])
    write_step(tmp_path, "01", "T", "y.py", {"G1": "another meaning"}, [fact("b", 2, "G1", "d")])
    with pytest.raises(ValueError, match="defined differently"):
        render(CFG, tmp_path)


def test_pipes_in_text_do_not_break_the_table(tmp_path):
    write_step(tmp_path, "00", "T", "x.py", {"G1": "g"}, [fact("k", 1, "G1", "largest |a - b| / b")])
    row = next(line for line in render(CFG, tmp_path).splitlines() if line.startswith("| G1 | k |"))
    assert row.count("|") - row.count("\\|") == 5  # exactly 4 cells
