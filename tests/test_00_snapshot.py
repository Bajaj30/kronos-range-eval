import json

import pandas as pd
import pytest

from lib.snapshot import SnapshotChanged, ensure_snapshot, load_raw, sha256_file, verify_snapshot

TICKERS = {"A": "^AAA", "B": "^BBB"}


class FakeSource:
    def __init__(self, empty=False):
        self.calls = 0
        self.empty = empty

    def __call__(self, symbol):
        self.calls += 1
        if self.empty:
            return pd.DataFrame()
        idx = pd.DatetimeIndex(["2025-01-06", "2025-01-07"], name="Date").tz_localize("Asia/Kolkata")
        return pd.DataFrame({"Open": [1.0, 2.0], "Close": [1.5, 2.5]}, index=idx)


def test_sha256_known_vector(tmp_path):
    p = tmp_path / "abc.txt"
    p.write_bytes(b"abc")
    assert sha256_file(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_one_changed_byte_changes_the_hash(tmp_path):
    p = tmp_path / "f.csv"
    p.write_bytes(b"Date,Close\n2025-01-06,100.0\n")
    before = sha256_file(p)
    p.write_bytes(b"Date,Close\n2025-01-06,100.1\n")
    assert sha256_file(p) != before


def test_second_run_verifies_instead_of_downloading(tmp_path):
    src = FakeSource()
    m1, created1 = ensure_snapshot(tmp_path / "snap", TICKERS, src, {"source": "fake"})
    m2, created2 = ensure_snapshot(tmp_path / "snap", TICKERS, src, {"source": "fake"})
    assert (created1, created2) == (True, False)
    assert src.calls == len(TICKERS)  # fetched once per ticker, never again
    assert m1 == m2


def test_tampered_file_is_refused(tmp_path):
    ensure_snapshot(tmp_path / "snap", TICKERS, FakeSource(), {})
    with open(tmp_path / "snap" / "A.csv", "a") as f:
        f.write("2025-01-08,3.0,3.5\n")
    with pytest.raises(SnapshotChanged):
        verify_snapshot(tmp_path / "snap")
    with pytest.raises(SnapshotChanged):
        load_raw(tmp_path / "snap", "B")  # any change anywhere refuses every read


def test_empty_source_leaves_no_snapshot(tmp_path):
    with pytest.raises(RuntimeError, match="no rows"):
        ensure_snapshot(tmp_path / "snap", TICKERS, FakeSource(empty=True), {})
    assert not (tmp_path / "snap").exists()
    assert not (tmp_path / "snap.partial").exists()


def test_leftover_partial_folder_is_rebuilt(tmp_path):
    (tmp_path / "snap.partial").mkdir()
    (tmp_path / "snap.partial" / "junk.csv").write_text("x")
    manifest, created = ensure_snapshot(tmp_path / "snap", TICKERS, FakeSource(), {})
    assert created and not (tmp_path / "snap.partial").exists()
    assert sorted(p.name for p in (tmp_path / "snap").iterdir()) == ["A.csv", "B.csv", "manifest.json"]


def test_manifest_records_rows_and_meta(tmp_path):
    manifest, _ = ensure_snapshot(tmp_path / "snap", TICKERS, FakeSource(), {"source": "fake"})
    on_disk = json.loads((tmp_path / "snap" / "manifest.json").read_text())
    assert on_disk == manifest
    assert manifest["source"] == "fake" and manifest["files"]["A"]["rows"] == 2
