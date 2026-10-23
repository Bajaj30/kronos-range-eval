"""FACTS.md generation. Each step writes out/facts/<step>.json; render() turns them, plus config, into FACTS.md.

Every fact must name a group defined in its file (playbook 5.1: a number without its group means nothing).
Output is deterministic: same inputs -> same bytes.
"""
import json
from pathlib import Path


def fact(key: str, value, group: str, desc: str) -> dict:
    return {"key": key, "value": value, "group": group, "desc": desc}


def write_step(facts_dir, step: str, title: str, source: str, groups: dict, facts: list, tables: list = ()) -> Path:
    doc = {"step": step, "title": title, "source": source, "groups": groups, "facts": list(facts), "tables": list(tables)}
    _validate(doc)
    path = Path(facts_dir) / f"{step}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True, default=str) + "\n")
    return path


def _validate(doc: dict) -> None:
    for f in doc["facts"]:
        if f["group"] not in doc["groups"]:
            raise ValueError(f"fact {f['key']!r} uses undefined group {f['group']!r}")
    for t in doc["tables"]:
        if t["group"] not in doc["groups"]:
            raise ValueError(f"table {t['title']!r} uses undefined group {t['group']!r}")
    keys = [(f["group"], f["key"]) for f in doc["facts"]]
    if len(keys) != len(set(keys)):
        raise ValueError(f"step {doc['step']}: duplicate (group, key) in facts")


def _cell(v) -> str:
    if isinstance(v, float):
        text = f"{v:.4g}" if abs(v) < 1e4 else f"{v:,.0f}"
    elif isinstance(v, (dict, list)):
        text = "`" + json.dumps(v, sort_keys=True) + "`"
    else:
        text = str(v)
    return text.replace("|", "\\|")  # a bare pipe would split the Markdown table cell


def _config_settings(config) -> list[tuple[str, str]]:
    """Upper-case config values, excluding paths (machine-specific, not facts)."""
    out = []
    for name, value in vars(config).items():
        if name.isupper() and not isinstance(value, Path):
            out.append((name, _cell(value)))
    return out


def render(config, facts_dir) -> str:
    docs = [json.loads(p.read_text()) for p in sorted(Path(facts_dir).glob("*.json"))]
    groups: dict[str, str] = {}
    for doc in docs:
        _validate(doc)
        for g, desc in doc["groups"].items():
            if g in groups and groups[g] != desc:
                raise ValueError(f"group {g!r} is defined differently in two steps")
            groups[g] = desc

    lines = [
        "# FACTS — generated, never hand-edited",
        "",
        "> Every number used in chat, the README, the resume or the site comes from this file.",
        "> Regenerate: `uv run python facts.py`. Inputs: `config.py` and `out/facts/*.json`.",
        "",
        "## Groups (what each number describes)",
        "",
        "| group | meaning |",
        "|---|---|",
        "| CONFIG | settings in `config.py` |",
    ]
    lines += [f"| {g} | {groups[g]} |" for g in sorted(groups)]
    lines += ["", "## Settings (group: CONFIG)", "", "| setting | value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in _config_settings(config)]

    for doc in docs:
        lines += ["", f"## Step {doc['step']} — {doc['title']}", "", f"Source: `{doc['source']}`", ""]
        lines += ["| group | key | value | meaning |", "|---|---|---|---|"]
        lines += [f"| {f['group']} | {f['key']} | {_cell(f['value'])} | {_cell(f['desc'])} |" for f in doc["facts"]]
        for t in doc["tables"]:
            lines += ["", f"**{t['title']}** (group: {t['group']})", ""]
            lines += ["| " + " | ".join(t["columns"]) + " |", "|" + "---|" * len(t["columns"])]
            lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in t["rows"]]
    return "\n".join(lines) + "\n"
