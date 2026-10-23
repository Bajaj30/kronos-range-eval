"""Raw snapshots: save exactly what the source returned, fingerprint it (sha256), verify it on every read."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


class SnapshotChanged(RuntimeError):
    """A snapshot file no longer matches the sha256 recorded when it was created."""


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_snapshot(snap_dir) -> dict:
    """Re-hash every file and compare with the manifest. Returns the manifest, or raises SnapshotChanged."""
    snap_dir = Path(snap_dir)
    manifest = json.loads((snap_dir / "manifest.json").read_text())
    for name, entry in manifest["files"].items():
        actual = sha256_file(snap_dir / entry["file"])
        if actual != entry["sha256"]:
            raise SnapshotChanged(f"{name}: sha256 {actual[:12]}… does not match manifest {entry['sha256'][:12]}…")
    return manifest


def ensure_snapshot(snap_dir, tickers: dict, fetch, meta: dict) -> tuple[dict, bool]:
    """Create the snapshot if it is missing; otherwise only verify it (never re-download).

    fetch(symbol) must return the source's DataFrame as received. Files are written to a `.partial`
    folder and renamed only after the manifest is written, so a crash never leaves a half snapshot.
    Returns (manifest, created).
    """
    snap_dir = Path(snap_dir)
    if (snap_dir / "manifest.json").exists():
        return verify_snapshot(snap_dir), False
    if snap_dir.exists():
        raise RuntimeError(f"{snap_dir} exists without a manifest; inspect and delete it by hand")

    tmp = snap_dir.with_name(snap_dir.name + ".partial")
    if tmp.exists():
        shutil.rmtree(tmp)  # left over from an interrupted pull; it was never a valid snapshot
    tmp.mkdir(parents=True)

    files = {}
    for name, symbol in tickers.items():
        df = fetch(symbol)
        if df is None or len(df) == 0:
            shutil.rmtree(tmp)
            raise RuntimeError(f"{symbol}: source returned no rows")
        path = tmp / f"{name}.csv"
        df.to_csv(path)  # the index (Yahoo's timestamp) is written exactly as returned
        files[name] = {"symbol": symbol, "file": path.name, "rows": len(df), "sha256": sha256_file(path)}

    manifest = {
        "snapshot_id": snap_dir.name,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **meta,
        "files": files,
    }
    (tmp / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    tmp.rename(snap_dir)
    return verify_snapshot(snap_dir), True


def load_raw(snap_dir, name: str) -> pd.DataFrame:
    """The only way later steps read raw data: verify the whole snapshot, then read one file as text columns."""
    manifest = verify_snapshot(snap_dir)
    return pd.read_csv(Path(snap_dir) / manifest["files"][name]["file"])
