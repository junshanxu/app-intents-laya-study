"""Choose one Laya confidence threshold using development fixtures only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge"))
from decision import LayaClient  # noqa: E402
from state import load_cases  # noqa: E402

def apply_gold(state: dict, case: dict, operation: str, arguments: dict) -> None:
    """Advance the ideal trajectory using the corpus's expected records."""
    if operation == "add_trip":
        identifier = arguments["trip_id"]
        state["trips"].append(next(item for item in case["expected"]["trips"] if item["id"] == identifier))
    elif operation == "create_task":
        identifier = arguments["task_id"]
        created = dict(next(item for item in case["expected"]["tasks"] if item["id"] == identifier))
        created["status"] = "open"  # Creation precedes any later completion action.
        state["tasks"].append(created)
    elif operation == "set_trip_status":
        next(item for item in state["trips"] if item["id"] == arguments["trip_id"])["status"] = arguments["status"]
    elif operation == "set_task_status":
        next(item for item in state["tasks"] if item["id"] == arguments["task_id"])["status"] = arguments["status"]
    elif operation == "reschedule_task":
        next(item for item in state["tasks"] if item["id"] == arguments["task_id"])["dueDate"] = arguments["due_date"]


def main() -> None:
    records = []
    client = LayaClient()
    for case in load_cases().values():
        if case["split"] != "dev":
            continue
        state = json.loads(json.dumps(case["initial"]))
        history = []
        for step, action in enumerate(case["oracle_actions"]):
            gold = action["operation"]
            decision = client.choose(case["prompt"], state, history)
            records.append({"task_id": case["task_id"], "step": step,
                            "choice": decision.action, "gold": gold,
                            "confidence": decision.confidence,
                            "correct": decision.action == gold})
            history.append(gold)
            apply_gold(state, case, gold, action["arguments"])
    # Predeclared criterion: accept the most development decisions among thresholds
    # with zero observed wrong accepted choices. Break ties toward higher threshold.
    candidates = [i / 100 for i in range(101)]
    valid = [threshold for threshold in candidates if not any(
        row["confidence"] >= threshold and not row["correct"] for row in records)]
    threshold = min(valid, key=lambda value: (-sum(row["confidence"] >= value for row in records), -value)) if valid else 1.01
    result = {"threshold": threshold, "criterion": "maximum dev coverage with zero accepted errors",
              "development_count": len(records),
              "accepted_count": sum(row["confidence"] >= threshold for row in records),
              "records": records}
    output = ROOT / "data" / "laya_dev_calibration.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Locked threshold {threshold:.2f}; accepted {result['accepted_count']}/{len(records)} development steps")


if __name__ == "__main__":
    main()
