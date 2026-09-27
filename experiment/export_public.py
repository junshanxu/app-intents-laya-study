"""Export synthetic, aggregate-ready run records without private traces or paths."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/runs/results.jsonl"
DESTINATION = ROOT / "data/results_public.jsonl"
FIELDS = (
    "run_id", "task_id", "template_id", "split", "repeat", "backend", "decision",
    "success", "mismatched_fields", "extra_changes", "invalid_calls", "failure_recovery",
    "tool_calls", "laya_calls", "app_latency_ms", "laya_latency_ms", "tool_latency_ms",
    "total_latency_ms", "model_turns", "timeout", "process_ok", "exit_code",
)
USAGE_FIELDS = (
    "input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit("No run data to export")
    rows = [json.loads(line) for line in SOURCE.read_text().splitlines()]
    rows = [row for row in rows if row["split"] in {"dev", "test"}]
    expected = {"dev": 24 * 4, "test": 72 * 3 * 4}
    for split, count in expected.items():
        actual = sum(row["split"] == split for row in rows)
        if actual != count:
            raise SystemExit(f"Expected {count} {split} rows, found {actual}")
    identifiers = [row["run_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise SystemExit("Duplicate run identifiers")
    public_rows = []
    for row in rows:
        public = {field: row[field] for field in FIELDS}
        usage = row.get("model_usage", {})
        public["model_usage"] = {field: usage[field] for field in USAGE_FIELDS if field in usage}
        public_rows.append(public)
    public_rows.sort(key=lambda row: row["run_id"])
    DESTINATION.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in public_rows))
    print(f"Wrote {len(public_rows)} synthetic records to {DESTINATION}")


if __name__ == "__main__":
    main()
