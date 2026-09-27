"""Small stdio MCP bridge for the two experimental tool surfaces.

STUDY_BACKEND=cli uses studyctl; STUDY_BACKEND=intents invokes saved macOS
Shortcuts with `shortcuts run`. The latter never calls AppIntent.perform directly.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from decision import LayaClient, snapshot

ROOT = Path(__file__).resolve().parents[1]
BACKEND = os.environ.get("STUDY_BACKEND", "cli")
DECISION_MODE = os.environ.get("STUDY_DECISION", "claude")
HISTORY: list[str] = []
RECOMMENDED: str | None = None
OPERATIONS = {
    "search_trips": ("Find trips whose destination contains the supplied text.", ["destination"]),
    "add_trip": ("Add a trip with an ID, destination and YYYY-MM-DD start date.", ["trip_id", "destination", "start_date"]),
    "set_trip_status": ("Set an existing trip status to booked or cancelled.", ["trip_id", "status"]),
    "find_tasks": ("Find tasks whose title contains the supplied text.", ["query"]),
    "create_task": ("Create a task, optionally linked to an existing trip.", ["task_id", "title", "due_date"]),
    "set_task_status": ("Set an existing task status to open or done.", ["task_id", "status"]),
    "reschedule_task": ("Change an existing task due date (YYYY-MM-DD).", ["task_id", "due_date"]),
}


def schema(operation: str) -> dict:
    description, required = OPERATIONS[operation]
    properties = {name: {"type": "string"} for name in required}
    if operation == "create_task":
        properties["trip_id"] = {"type": "string"}
    return {
        "name": operation,
        "description": description,
        "inputSchema": {"type": "object", "properties": properties, "required": required, "additionalProperties": False},
    }


def trace(entry: dict) -> None:
    location = os.environ.get("STUDY_TRACE_PATH")
    if not location:
        return
    path = Path(location)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")


def rejected(operation: str, reason: str) -> tuple[str, bool]:
    trace({"operation": operation, "backend": BACKEND, "failed": True, "latency_ms": 0,
           "rejection": reason})
    return reason, True


def run_tool(operation: str, arguments: dict) -> tuple[str, bool]:
    global RECOMMENDED
    if operation == "run_studyctl":
        if BACKEND != "cli":
            return rejected("run_studyctl", "CLI command tool is unavailable in the App Intents arm")
        try:
            parts = shlex.split(arguments["command"])
            if len(parts) != 3 or parts[0] != "studyctl":
                raise ValueError("Use: studyctl OPERATION JSON_ARGUMENTS")
            parsed = json.loads(parts[2])
            if not isinstance(parsed, dict):
                raise ValueError("JSON_ARGUMENTS must be an object")
        except (KeyError, TypeError, ValueError) as error:
            return rejected("invalid_cli_command", f"Invalid command: {error}")
        return run_tool(parts[1], parsed)
    if operation == "recommend_action":
        if DECISION_MODE != "laya":
            return "Laya decision mode is not active", True
        task = os.environ.get("STUDY_TASK_PROMPT", "")
        if not task:
            return "Task prompt is missing", True
        started = time.perf_counter()
        try:
            choice = LayaClient().choose(task, snapshot(), HISTORY)
            threshold = float(os.environ.get("STUDY_LAYA_THRESHOLD", "1.0"))
            RECOMMENDED = choice.action if choice.confidence >= threshold else None
            response = {"recommended_action": RECOMMENDED, "fallback_to_claude": RECOMMENDED is None,
                        "confidence": choice.confidence, "threshold": threshold, "model": choice.model}
            trace({"operation": "recommend_action", "backend": "laya", "failed": False,
                   "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                   "choice": choice.action, "confidence": choice.confidence,
                   "accepted": RECOMMENDED is not None, "usage": choice.usage})
            return json.dumps(response), False
        except Exception as error:
            RECOMMENDED = None
            trace({"operation": "recommend_action", "backend": "laya", "failed": True,
                   "latency_ms": round((time.perf_counter() - started) * 1000, 2)})
            return f"Laya unavailable; use Claude planning: {error}", False
    if operation not in OPERATIONS:
        return rejected("invalid_operation", f"Unknown operation: {operation}")
    if DECISION_MODE == "laya" and RECOMMENDED is not None and operation != RECOMMENDED:
        return rejected(operation, f"Laya selected {RECOMMENDED}; call that action next, or call recommend_action again after state changes")
    if not isinstance(arguments, dict):
        return rejected(operation, "Arguments must be a JSON object")
    allowed = set(schema(operation)["inputSchema"]["properties"])
    required = set(OPERATIONS[operation][1])
    if not required.issubset(arguments) or set(arguments) - allowed or any(not isinstance(v, str) for v in arguments.values()):
        return rejected(operation, "Invalid or missing tool arguments")
    started = time.perf_counter()
    try:
        if BACKEND == "cli":
            command = [str(ROOT / "bin/studyctl"), operation, json.dumps(arguments)]
            process = subprocess.run(command, capture_output=True, text=True, timeout=30)
            result = process.stdout.strip() if process.returncode == 0 else process.stderr.strip()
            failed = process.returncode != 0
        elif BACKEND == "intents":
            with tempfile.TemporaryDirectory(prefix="study-shortcuts-") as directory:
                input_path = Path(directory) / "input.json"
                output_path = Path(directory) / "output.txt"
                input_path.write_text(json.dumps(arguments, ensure_ascii=False))
                command = ["shortcuts", "run", f"AI_{operation}", "-i", str(input_path), "-o", str(output_path)]
                process = subprocess.run(command, capture_output=True, text=True, timeout=30)
                failed = process.returncode != 0
                result = process.stderr.strip() if failed else output_path.read_text().strip()
        else:
            return rejected(operation, f"Unknown backend: {BACKEND}")
    except (OSError, subprocess.TimeoutExpired) as error:
        result, failed = str(error), True
    trace({"operation": operation, "backend": BACKEND, "arguments": arguments,
           "failed": failed, "latency_ms": round((time.perf_counter() - started) * 1000, 2)})
    HISTORY.append(operation)
    RECOMMENDED = None
    return result, failed


def dispatch(message: dict) -> dict | None:
    method = message.get("method")
    identifier = message.get("id")
    if identifier is None:
        return None
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "app-intents-laya-study", "version": "0.1.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        if BACKEND == "intents":
            available = [schema(operation) for operation in OPERATIONS]
        else:
            available = [{"name": "run_studyctl",
                          "description": "Run the synthetic studyctl command. Syntax: studyctl OPERATION JSON_ARGUMENTS. Operations: search_trips(destination), add_trip(trip_id,destination,start_date), set_trip_status(trip_id,status), find_tasks(query), create_task(task_id,title,due_date, optional trip_id), set_task_status(task_id,status), reschedule_task(task_id,due_date). Example: studyctl search_trips '{\"destination\":\"Kyoto\"}'. No shell features are supported.",
                          "inputSchema": {"type": "object", "properties": {"command": {"type": "string"}},
                                          "required": ["command"], "additionalProperties": False}}]
        if DECISION_MODE == "laya":
            available.append({"name": "recommend_action", "description": "Ask local Laya to select the next app action from current state. Call before each app action. Low confidence delegates planning to Claude.",
                              "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}})
        result = {"tools": available}
    elif method == "tools/call":
        params = message.get("params", {})
        content, failed = run_tool(params.get("name", ""), params.get("arguments", {}))
        result = {"content": [{"type": "text", "text": content}], "isError": failed}
    else:
        return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32601, "message": f"Unknown method: {method}"}}
    return {"jsonrpc": "2.0", "id": identifier, "result": result}


def main() -> None:
    for line in sys.stdin:
        try:
            response = dispatch(json.loads(line))
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
        except Exception as error:
            # Keep stdout limited to MCP frames; details may go to stderr.
            print(f"MCP error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
