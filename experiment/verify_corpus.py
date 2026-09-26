"""Execute every authored oracle through the shared Swift CLI and grade state."""
from __future__ import annotations

import json
import subprocess

from state import ROOT, load_cases, reset, score, snapshot


def main() -> None:
    executable = ROOT / "bin/studyctl"
    if not executable.exists():
        raise SystemExit("Build the Swift CLI with scripts/build-cli.sh first")
    cases = load_cases()
    for case in cases.values():
        reset(case)
        for action in case["oracle_actions"]:
            result = subprocess.run(
                [str(executable), action["operation"], json.dumps(action["arguments"])],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode:
                raise RuntimeError(f"{case['task_id']} {action['operation']}: {result.stderr.strip()}")
        outcome = score(case, snapshot())
        if not outcome["success"] or outcome["extra_changes"]:
            raise RuntimeError(f"{case['task_id']} oracle disagrees with scorer: {outcome}")
    print(f"Verified {len(cases)} authored trajectories through the shared Swift CLI")


if __name__ == "__main__":
    main()
