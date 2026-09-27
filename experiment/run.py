"""Run the preregistered 2x2 paired experiment after the Shortcuts gate passes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from state import ROOT, load_cases, reset, score, snapshot

GROUPS = [("intents", "claude"), ("intents", "laya"), ("cli", "claude"), ("cli", "laya")]
INTENT_TOOLS = ["search_trips", "add_trip", "set_trip_status", "find_tasks", "create_task", "set_task_status", "reschedule_task"]
MODEL = "doubao-seed-2.1-pro"
BASE_URL = "https://ark.cn-beijing.volces.com/api/coding"
RUN_DIR = ROOT / "data/runs"


def command_output(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()


def lock_versions() -> dict:
    laya_python = Path(os.environ.get("STUDY_LAYA_PYTHON", str(Path.home() / "Code/laya-local-deploy/.venv/bin/python")))
    laya_version = command_output([str(laya_python), "-c", "import importlib.metadata; print(importlib.metadata.version('laya'))"])
    laya_ref = Path(os.environ.get("STUDY_LAYA_CACHE_REF", str(
        Path.home() / ".cache/huggingface/hub/models--convaiinnovations--laya/refs/main")))
    if not laya_ref.exists():
        raise RuntimeError("Laya checkpoint revision is unavailable; set STUDY_LAYA_CACHE_REF")
    data = {
        "macos": platform.mac_ver()[0],
        "xcode": command_output(["xcodebuild", "-version"]),
        "claude_code": command_output(["claude", "--version"]),
        "laya": laya_version,
        "laya_hf_revision": laya_ref.read_text().strip(),
        "model": MODEL,
        "coding_plan_base_url": BASE_URL,
        "corpus_sha256": hashlib.sha256((ROOT / "data/tasks.json").read_bytes()).hexdigest(),
        "calibration_sha256": hashlib.sha256((ROOT / "data/laya_dev_calibration.json").read_bytes()).hexdigest(),
        "implementation_sha256": hashlib.sha256(b"".join(
            (ROOT / name).read_bytes() for name in (
                "project.yml", "Shared/StudyStore.swift", "TripLedger/TripIntents.swift",
                "TripLedger/TripLedgerApp.swift", "TaskBoard/TaskIntents.swift", "TaskBoard/TaskBoardApp.swift",
                "CLI/main.swift", "bridge/decision.py", "bridge/mcp_server.py", "experiment/run.py",
                "experiment/state.py",
            )
        )).hexdigest(),
    }
    lock = ROOT / "data/version_lock.json"
    if lock.exists() and json.loads(lock.read_text()) != data:
        raise RuntimeError("Version lock changed. Investigate before continuing the test split.")
    lock.write_text(json.dumps(data, indent=2) + "\n")
    return data


def shortcuts_gate() -> None:
    """A read and write shortcut must genuinely execute through Shortcuts."""
    cases = load_cases()
    case = cases["T00V0"]
    reset(case)
    fixture_trip_id = case["initial"]["trips"][0]["id"]
    # The wrappers must be supplied by the Shortcuts editor. Merely finding the
    # app actions in its library does not pass this gate.
    for operation, args, expected_fragment in [
        ("search_trips", {"destination": "Kyoto"}, fixture_trip_id),
        ("create_task", {"task_id": "gate-task", "title": "Gate task", "due_date": "2027-01-15", "trip_id": fixture_trip_id}, "gate-task"),
    ]:
        with tempfile.TemporaryDirectory(prefix="study-gate-") as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.txt"
            input_path.write_text(json.dumps(args))
            try:
                result = subprocess.run(["shortcuts", "run", f"AI_{operation}", "-i", str(input_path), "-o", str(output_path)],
                                        capture_output=True, text=True, timeout=30)
            except subprocess.TimeoutExpired as error:
                raise RuntimeError(f"Shortcuts system execution timed out for {operation}") from error
            if result.returncode or not output_path.exists():
                raise RuntimeError(f"Shortcuts system execution failed for {operation}: {result.stderr.strip()[:200]}")
            if expected_fragment not in output_path.read_text():
                raise RuntimeError(f"Shortcuts {operation} output lacks expected record {expected_fragment}")
    state = snapshot()
    if not any(item["id"] == "gate-task" for item in state["tasks"]):
        raise RuntimeError("Write shortcut returned without changing application state")
    print("Shortcuts read/write gate passed")


def all_shortcuts_gate() -> None:
    """Require every experiment action to work through a saved Shortcut."""
    shortcuts_gate()
    operations = [
        ("add_trip", {"trip_id": "gate-trip", "destination": "Oslo", "start_date": "2027-01-16"}, "gate-trip"),
        ("set_trip_status", {"trip_id": "gate-trip", "status": "cancelled"}, "cancelled"),
        ("find_tasks", {"query": "Gate task"}, "gate-task"),
        ("set_task_status", {"task_id": "gate-task", "status": "done"}, "done"),
        ("reschedule_task", {"task_id": "gate-task", "due_date": "2027-01-17"}, "2027-01-17"),
    ]
    for operation, arguments, expected in operations:
        with tempfile.TemporaryDirectory(prefix="study-gate-all-") as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.txt"
            input_path.write_text(json.dumps(arguments))
            try:
                result = subprocess.run(["shortcuts", "run", f"AI_{operation}", "-i", str(input_path), "-o", str(output_path)],
                                        capture_output=True, text=True, timeout=30)
            except subprocess.TimeoutExpired as error:
                raise RuntimeError(f"Shortcuts system execution timed out for {operation}") from error
            if result.returncode or not output_path.exists() or expected not in output_path.read_text():
                raise RuntimeError(f"Shortcuts system execution failed for {operation}: {result.stderr.strip()[:200]}")
    state = snapshot()
    trip = next((item for item in state["trips"] if item["id"] == "gate-trip"), None)
    task = next((item for item in state["tasks"] if item["id"] == "gate-task"), None)
    if not trip or trip["destination"] != "Oslo" or trip["status"] != "cancelled":
        raise RuntimeError("Trip wrappers returned without the expected final application state")
    if not task or task["status"] != "done" or task["dueDate"] != "2027-01-17":
        raise RuntimeError("Task wrappers returned without the expected final application state")
    print("All seven Shortcuts action wrappers passed")


def run_one(case: dict, backend: str, decision: str, repeat: int, threshold: float, key: str) -> dict:
    reset(case)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    run_id = f"{case['task_id']}-{backend}-{decision}-r{repeat}"
    trace_path = RUN_DIR / f"{run_id}.tools.jsonl"
    if trace_path.exists():
        trace_path.unlink()
    config = {"mcpServers": {"study": {
        "command": sys.executable,
        "args": [str(ROOT / "bridge/mcp_server.py")],
        "env": {"STUDY_BACKEND": backend, "STUDY_DECISION": decision,
                "STUDY_TASK_PROMPT": case["prompt"], "STUDY_LAYA_THRESHOLD": str(threshold),
                "STUDY_TRACE_PATH": str(trace_path),
                "STUDY_LAYA_URL": os.environ.get("STUDY_LAYA_URL", "http://127.0.0.1:8765/v1/systemone")},
    }}}
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    env.update({"ANTHROPIC_AUTH_TOKEN": key, "ANTHROPIC_BASE_URL": BASE_URL,
                "ANTHROPIC_MODEL": MODEL, "ANTHROPIC_DEFAULT_SONNET_MODEL": MODEL,
                "ANTHROPIC_DEFAULT_OPUS_MODEL": MODEL, "ANTHROPIC_DEFAULT_HAIKU_MODEL": MODEL})
    env["CLAUDE_CODE_SUBAGENT_MODEL"] = MODEL
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    prompt = (
        "You are operating two synthetic macOS study apps. Use only the study MCP tools. "
        "Do not use shell commands, files, web, or other apps. Finish the task, then stop. "
        "If a tool fails, correct the call or report that you cannot finish. "
        + ("Before each app action, call recommend_action. If it returns a recommendation, perform that action next; if it delegates, plan yourself. " if decision == "laya" else "")
        + ("The CLI surface exposes one run_studyctl tool. Compose only studyctl commands with JSON arguments as described by that tool. " if backend == "cli" else "The App Intents surface exposes typed actions through macOS Shortcuts. ")
        + "User task: " + case["prompt"]
    )
    with tempfile.TemporaryDirectory(prefix="study-config-") as directory:
        config_path = Path(directory) / "mcp.json"
        config_path.write_text(json.dumps(config))
        tool_names = ["run_studyctl"] if backend == "cli" else list(INTENT_TOOLS)
        if decision == "laya":
            tool_names.append("recommend_action")
        allowed = ",".join("mcp__study__" + name for name in tool_names)
        command = ["claude", "-p", prompt, "--output-format", "json", "--model", MODEL,
                   "--mcp-config", str(config_path), "--strict-mcp-config", "--setting-sources", "project",
                   "--tools", "", "--allowedTools", allowed,
                   "--permission-mode", "dontAsk", "--no-session-persistence"]
        started = time.perf_counter()
        try:
            process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
            timeout = False
        except subprocess.TimeoutExpired:
            process = None
            timeout = True
        total_ms = round((time.perf_counter() - started) * 1000, 2)
    observed = snapshot()
    outcome = score(case, observed)
    state_path = RUN_DIR / f"{run_id}.final-state.json"
    state_path.write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n")
    events = [json.loads(line) for line in trace_path.read_text().splitlines()] if trace_path.exists() else []
    response = {}
    if process and process.returncode == 0:
        try:
            response = json.loads(process.stdout)
        except json.JSONDecodeError:
            pass
    app_calls = [event for event in events if event["operation"] != "recommend_action"]
    laya_calls = [event for event in events if event["operation"] == "recommend_action"]
    failures = [event for event in app_calls if event["failed"]]
    record = {
        "run_id": run_id, "task_id": case["task_id"], "template_id": case["template_id"],
        "split": case["split"], "repeat": repeat, "backend": backend, "decision": decision,
        **outcome, "invalid_calls": len(failures),
        "failure_recovery": bool(failures and outcome["success"]),
        "tool_calls": len(app_calls), "laya_calls": len(laya_calls),
        "app_latency_ms": round(sum(event["latency_ms"] for event in app_calls), 2),
        "laya_latency_ms": round(sum(event["latency_ms"] for event in laya_calls), 2),
        "tool_latency_ms": round(sum(event["latency_ms"] for event in events), 2),
        "total_latency_ms": total_ms, "model_usage": response.get("usage", {}),
        "model_turns": response.get("num_turns"), "timeout": timeout,
        "process_ok": process is not None and process.returncode == 0,
        "exit_code": process.returncode if process else None,
    }
    with (RUN_DIR / "results.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["gate", "gate-all", "dev", "test"])
    parser.add_argument("--limit", type=int, default=0, help="Limit tasks for a development smoke run")
    args = parser.parse_args()
    if args.phase == "gate":
        shortcuts_gate()
        return
    if args.phase == "gate-all":
        all_shortcuts_gate()
        return
    key = os.environ.get("ARK_CODING_PLAN_API_KEY", "")
    if not key:
        raise SystemExit("Set ARK_CODING_PLAN_API_KEY only in the experiment process")
    lock_versions()
    all_shortcuts_gate()
    calibration = json.loads((ROOT / "data/laya_dev_calibration.json").read_text())
    threshold = float(calibration["threshold"])
    cases = [case for case in load_cases().values() if case["split"] == args.phase]
    if args.limit:
        cases = cases[: args.limit]
    repeats = 3 if args.phase == "test" else 1
    existing = set()
    results_path = RUN_DIR / "results.jsonl"
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            row = json.loads(line)
            if row["split"] == args.phase:
                existing.add((row["task_id"], row["repeat"], row["backend"], row["decision"]))
    for case in cases:
        for repeat in range(repeats):
            order = list(GROUPS)
            random.Random(f"20260926:{case['task_id']}:{repeat}").shuffle(order)
            for backend, decision in order:
                if (case["task_id"], repeat, backend, decision) in existing:
                    continue
                result = run_one(case, backend, decision, repeat, threshold, key)
                print(result["run_id"], "success" if result["success"] else "failed", flush=True)


if __name__ == "__main__":
    main()
