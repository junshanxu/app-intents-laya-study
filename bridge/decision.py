"""Interchangeable next-action decision interface for Laya and future Jev."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.request import Request, urlopen

STATE_DIR = Path.home() / "Library/Application Support/AppIntentsLayaStudy"
CANDIDATES = {
    "search_trips": "Find existing trips by destination to discover their IDs and status",
    "add_trip": "Create a new trip that does not yet exist",
    "set_trip_status": "Change the status of an existing trip",
    "find_tasks": "Find existing tasks by title to discover their IDs and status",
    "create_task": "Create a new to-do task that does not yet exist",
    "set_task_status": "Change the status of an existing task",
    "reschedule_task": "Change the due date of an existing task",
}


@dataclass(frozen=True)
class Decision:
    action: str | None
    confidence: float
    model: str
    usage: dict
    raw: dict


class DecisionClient(Protocol):
    def choose(self, task: str, state: dict, history: list[str]) -> Decision: ...


class LayaClient:
    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint or os.environ.get("STUDY_LAYA_URL", "http://127.0.0.1:8765/v1/systemone")

    def choose(self, task: str, state: dict, history: list[str]) -> Decision:
        # The initial decision only needs to separate locating existing records
        # from creating a new trip. This candidate reduction was fixed on dev.
        first = not history
        candidates = {key: CANDIDATES[key] for key in ("search_trips", "find_tasks", "add_trip")} if first else CANDIDATES
        payload = {
            "model": "multilingual",
            "state": {"user_task": task, "current_state": state, "actions_so_far": history},
            "questions": {
                "next_action": {
                    "type": "choice",
                    "instructions": ("Choose the FIRST agent tool action. For changing an existing record, find it before updating it. For a requested new trip, create it." if first else
                                     "Which single app action should an assistant perform next to fulfill the user task? Choose based on the current state and actions already taken. Existing records should be found before updating them."),
                    "criteria": candidates,
                }
            },
        }
        request = Request(self.endpoint, data=json.dumps(payload).encode(), headers={"content-type": "application/json"})
        with urlopen(request, timeout=60) as response:
            result = json.load(response)
        answer = result["answers"]["next_action"]
        return Decision(
            action=answer.get("choice"),
            confidence=float(answer.get("answer_confidence", 0.0)),
            model=result.get("routing", {}).get("model", result.get("model", "unknown")),
            usage=result.get("usage", {}),
            raw=answer,
        )


class JevClient:
    def choose(self, task: str, state: dict, history: list[str]) -> Decision:
        raise RuntimeError("Jev credentials are not configured; Jev is excluded from round one")


def snapshot() -> dict:
    return {kind: json.loads((STATE_DIR / f"{kind}.json").read_text()) for kind in ("trips", "tasks")}
