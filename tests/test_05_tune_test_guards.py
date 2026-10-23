"""Chunks 6-7: calibration and choice wiring, and the guards around tuning and the one test run."""
import subprocess

import numpy as np
import pandas as pd
import pytest

import config
from lib import evaluate as E
from lib import metrics as M
from lib.provenance import AlreadyRun, NotPreregistered, git_state, prereg_record, start_run


def table(n=60, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.uniform(0.5, 2.0, n)
    return pd.DataFrame({"date": pd.bdate_range("2025-09-01", periods=n), "tr_pct": y,
                         "atr_prev_pct": y * rng.uniform(0.6, 1.4, n), "naive_prev_pct": y * rng.uniform(0.3, 2.0, n),
                         "kronos_median": y / 2, "kronos_p10": y / 4, "kronos_p90": y, "kronos_distinct": 12})


def test_every_method_is_calibrated_by_the_same_functions():
    t = table()
    cal = E.fit(t)
    assert cal["kronos"] == M.fit_kronos(t["tr_pct"], t["kronos_median"])
    assert cal["atr"] == M.fit_baseline(t["tr_pct"], t["atr_prev_pct"], config.BAND)
    assert cal["naive"] == M.fit_baseline(t["tr_pct"], t["naive_prev_pct"], config.BAND)
    assert E.ALPHA == 0.2


def test_scores_use_calibrated_forecasts():
    t = table()
    cal = E.fit(t)
    s = E.score_all(t, cal, with_ci=True)
    assert cal["kronos"]["scale"] == pytest.approx(2.0)  # median actual / median forecast, forecast = y / 2
    assert s["kronos"]["mae"] == pytest.approx(0.0, abs=1e-12) and s["kronos"]["coverage"] == 1.0
    assert s["kronos"]["mae_raw"] == pytest.approx(np.mean(t["tr_pct"] / 2))
    assert s["kronos_vs_atr"]["ratio"] == pytest.approx(0.0, abs=1e-12)
    assert s["kronos_vs_atr"]["ci_low"] <= s["kronos_vs_atr"]["ratio"] <= s["kronos_vs_atr"]["ci_high"]
    c = E.apply(t, cal)
    np.testing.assert_allclose(c["atr_lo"], cal["atr"]["band_lo"] * t["atr_prev_pct"])


def test_choice_takes_the_lowest_mean_ratio_and_breaks_ties_by_grid_order():
    grid = [[0.6, 0.9], [0.8, 0.9], [1.0, 0.9]]
    assert E.choose({(0.6, 0.9): 0.99, (0.8, 0.9): 0.97, (1.0, 0.9): 0.98}, grid) == [0.8, 0.9]
    assert E.choose({(0.6, 0.9): 0.97, (0.8, 0.9): 0.97, (1.0, 0.9): 0.98}, grid) == [0.6, 0.9]


def test_second_test_run_is_refused_unless_forced_and_then_counted(tmp_path):
    log = tmp_path / "out" / "test_runs.log"
    assert start_run(log, force=False, note="a") == 1
    with pytest.raises(AlreadyRun, match="already ran 1"):
        start_run(log, force=False, note="b")
    assert start_run(log, force=True, note="c") == 2
    assert log.read_text().splitlines() == ["run 1 a", "run 2 c"]


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    remote, work = tmp_path / "remote.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    git(work, "remote", "add", "origin", str(remote))
    (work / "code.py").write_text("x = 1\n")
    (work / "out").mkdir()
    (work / "out" / "facts.json").write_text("{}\n")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "init")
    return work


def test_git_state_ignores_generated_outputs_only(repo):
    assert git_state(repo)["dirty"] is False
    (repo / "out" / "facts.json").write_text('{"a": 1}\n')
    assert git_state(repo, ignore=("out/",))["dirty"] is False
    assert git_state(repo)["edited"] == ["out/facts.json"]
    (repo / "code.py").write_text("x = 2\n")
    assert git_state(repo, ignore=("out/",))["edited"] == ["code.py"]


def test_prereg_must_be_committed_unchanged_and_pushed(repo):
    with pytest.raises(NotPreregistered, match="does not exist"):
        prereg_record(repo)
    (repo / "PREREG.md").write_text("plan\n")
    with pytest.raises(NotPreregistered, match="never been committed"):
        prereg_record(repo)
    git(repo, "add", "PREREG.md")
    git(repo, "commit", "-q", "-m", "prereg")
    with pytest.raises(NotPreregistered, match="not on any remote"):
        prereg_record(repo)
    git(repo, "push", "-q", "origin", "main")
    rec = prereg_record(repo)
    assert len(rec["commit"]) == 40 and len(rec["sha256"]) == 64
    (repo / "PREREG.md").write_text("plan, edited after the fact\n")
    with pytest.raises(NotPreregistered, match="uncommitted edits"):
        prereg_record(repo)
