"""Reset and score synthetic app state independently of the agent."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = Path.home() / "Library/Application Support/AppIntentsLayaStudy"


def load_cases() -> dict[str, dict]:
    return {case["task_id"]: case for case in json.loads((ROOT / "data/tasks.json").read_text())}


def reset(case: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for kind in ("trips", "tasks"):
        target = STATE_DIR / f"{kind}.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(case["initial"][kind], ensure_ascii=False))
        os.replace(temporary, target)


def snapshot() -> dict:
    return {kind: json.loads((STATE_DIR / f"{kind}.json").read_text()) for kind in ("trips", "tasks")}


def canonical(state: dict) -> dict:
    # Swift Codable omits nil Optional fields when it rewrites the JSON file;
    # fixture JSON expresses the same value as an explicit null.
    trips = sorted((dict(item) for item in state["trips"]), key=lambda entry: entry["id"])
    tasks = []
    for item in state["tasks"]:
        normalized = dict(item)
        normalized.setdefault("tripID", None)
        tasks.append(normalized)
    return {"trips": trips, "tasks": sorted(tasks, key=lambda entry: entry["id"])}


def score(case: dict, observed: dict) -> dict:
    expected = canonical(case["expected"])
    actual = canonical(observed)
    initial = canonical(case["initial"])
    mismatched = 0
    extra = 0
    for kind in ("trips", "tasks"):
        wanted = {item["id"]: item for item in expected[kind]}
        found = {item["id"]: item for item in actual[kind]}
        before = {item["id"]: item for item in initial[kind]}
        for identifier in wanted.keys() | found.keys():
            if identifier not in wanted or identifier not in found:
                mismatched += 1
            elif wanted[identifier] != found[identifier]:
                mismatched += sum(wanted[identifier].get(key) != found[identifier].get(key) for key in wanted[identifier].keys() | found[identifier].keys())
            if identifier not in wanted and identifier in found:
                extra += 1
            elif identifier in before and identifier in found and identifier in wanted:
                extra += sum(
                    before[identifier].get(key) == wanted[identifier].get(key)
                    and found[identifier].get(key) != before[identifier].get(key)
                    for key in before[identifier].keys() | wanted[identifier].keys() | found[identifier].keys()
                )
            elif identifier in wanted and identifier in found and identifier not in before:
                extra += sum(wanted[identifier].get(key) != found[identifier].get(key)
                             for key in wanted[identifier].keys() | found[identifier].keys())
    return {"success": actual == expected, "mismatched_fields": mismatched, "extra_changes": extra}
