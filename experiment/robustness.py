"""Post hoc audit of ambiguous task links and invalid tool calls.

This does not replace the preregistered exact-state outcome in analyze.py.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from state import ROOT, canonical, load_cases

RUN_DIR = ROOT / "data/runs"
OUTPUT = ROOT / "data/robustness.json"


def linked_followup_equivalent(case: dict, observed: dict) -> bool:
    """Accept an optional link only to the trip this task asked to cancel."""
    expected = canonical(case["expected"])
    actual = canonical(observed)
    if actual == expected:
        return True
    before_trips = {trip["id"]: trip for trip in case["initial"]["trips"]}
    changed = [trip["id"] for trip in expected["trips"]
               if before_trips[trip["id"]]["status"] != trip["status"]]
    if len(changed) != 1:
        return False
    before_tasks = {task["id"] for task in case["initial"]["tasks"]}
    candidate = json.loads(json.dumps(actual))
    for task in candidate["tasks"]:
        if task["id"] not in before_tasks and task.get("tripID") == changed[0]:
            task["tripID"] = None
    return candidate == expected


def main() -> None:
    cases = load_cases()
    rows = [json.loads(line) for line in (RUN_DIR / "results.jsonl").read_text().splitlines()]
    rows = [row for row in rows if row["split"] == "test"]
    if len(rows) != 864 or len({row["run_id"] for row in rows}) != 864:
        raise SystemExit("Require the complete, unique 864-run test set")
    exact = Counter()
    sensitivity = Counter()
    differences = []
    invalid = Counter()
    status_terms = Counter()
    laya_calls = accepted = 0
    for row in rows:
        arm = f"{row['backend']}_{row['decision']}"
        exact[arm] += bool(row["success"])
        observed = json.loads((RUN_DIR / f"{row['run_id']}.final-state.json").read_text())
        equivalent = linked_followup_equivalent(cases[row["task_id"]], observed)
        sensitivity[arm] += equivalent
        if equivalent and not row["success"]:
            differences.append(row["run_id"])
        for line in (RUN_DIR / f"{row['run_id']}.tools.jsonl").read_text().splitlines():
            event = json.loads(line)
            if event["operation"] == "recommend_action":
                laya_calls += 1
                accepted += bool(event.get("accepted"))
            elif event.get("failed"):
                invalid[(arm, event["operation"])] += 1
                if event["operation"] == "set_task_status":
                    status_terms[event.get("arguments", {}).get("status", "")] += 1
    report = {
        "label": "post hoc sensitivity; original exact-state outcome remains primary",
        "exact_success_counts": dict(exact),
        "optional_target_trip_link_allowed_success_counts": dict(sensitivity),
        "reclassified_link_only_failures": len(differences),
        "remaining_failures": len(rows) - sum(sensitivity.values()),
        "invalid_calls_by_arm_and_operation": {
            f"{arm}:{operation}": count for (arm, operation), count in sorted(invalid.items())
        },
        "failed_task_status_terms": dict(status_terms),
        "laya_consultations": laya_calls,
        "laya_accepted_recommendations": accepted,
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
