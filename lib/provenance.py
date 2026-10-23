"""Who made a result, from what (Chunks 6-7): git state, PREREG commit, package versions, the run counter."""
import json
import platform
import subprocess
from pathlib import Path

from lib.snapshot import sha256_file


class NotPreregistered(RuntimeError):
    """PREREG.md is missing, edited since its commit, or its commit is not on GitHub."""


class AlreadyRun(RuntimeError):
    """The test has run before; a rerun must be forced and is counted."""


def _git(repo, *args) -> str:
    # rstrip, not strip: `status --porcelain` lines start with a status column that may be a space.
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.rstrip("\n")


def git_state(repo, ignore=()) -> dict:
    """HEAD commit and the tracked files with uncommitted edits, except paths starting with an `ignore` prefix
    (generated outputs such as out/ and FACTS.md)."""
    lines = _git(repo, "status", "--porcelain", "--untracked-files=no").splitlines()
    edited = sorted(l[3:] for l in lines if not l[3:].startswith(tuple(ignore)))
    return {"commit": _git(repo, "rev-parse", "HEAD"), "dirty": bool(edited), "edited": edited}


def prereg_record(repo, path="PREREG.md") -> dict:
    """The commit that last changed PREREG.md. Refuses if the file is uncommitted, edited since, or not pushed:
    tuning and testing may only start once the plan is public (ground rule 3)."""
    file = Path(repo) / path
    if not file.exists():
        raise NotPreregistered(f"{path} does not exist")
    commit = _git(repo, "log", "-1", "--format=%H", "--", path)
    if not commit:
        raise NotPreregistered(f"{path} has never been committed")
    if _git(repo, "status", "--porcelain", "--", path):
        raise NotPreregistered(f"{path} has uncommitted edits")
    if not _git(repo, "branch", "-r", "--contains", commit):
        raise NotPreregistered(f"commit {commit[:12]} with {path} is not on any remote branch; push it first")
    return {"commit": commit, "committed_utc": _git(repo, "log", "-1", "--format=%cI", commit),
            "sha256": sha256_file(file)}


def versions() -> dict:
    import huggingface_hub
    import numpy
    import pandas
    import torch

    return {"python": platform.python_version(), "machine": platform.machine(), "torch": torch.__version__,
            "numpy": numpy.__version__, "pandas": pandas.__version__, "huggingface_hub": huggingface_hub.__version__,
            "torch_threads": torch.get_num_threads()}


def start_run(log_path, force: bool, note: str) -> int:
    """Count a test run BEFORE it touches the test window, in an append-only log (in git), so even a run that
    crashes halfway is counted. The first run is 1; later runs are refused unless forced."""
    log_path = Path(log_path)
    previous = len(log_path.read_text().splitlines()) if log_path.exists() else 0
    if previous and not force:
        raise AlreadyRun(f"the test already ran {previous} time(s); rerun with --force (it will be counted)")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"run {previous + 1} {note}\n")
    return previous + 1
