"""Deterministic synthetic task corpus: 24 templates x 4 fixtures."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "tasks.json"

PHRASINGS = [
    [
        "Find the {destination} trip starting {old_start}, then create task {new_task_id} titled '{new_title}' due {new_date} and link it to that trip.",
        "For my {destination} trip starting {old_start}, add a linked to-do: ID {new_task_id}, title '{new_title}', due {new_date}.",
        "Look up the {destination} trip that starts {old_start}. Attach a new task '{new_title}' (ID {new_task_id}) due {new_date}.",
        "I need a task for the {destination} trip beginning {old_start}. Find that trip and add '{new_title}' with ID {new_task_id}, due {new_date}.",
    ],
    [
        "Cancel the {destination} trip starting {old_start} and mark its linked booking task '{existing_title}' done.",
        "My {destination} trip starting {old_start} is cancelled. Update it and finish its existing to-do '{existing_title}'.",
        "Find the {destination} trip beginning {old_start}, cancel it, and complete the '{existing_title}' task linked to it.",
        "Please cancel the booked {destination} trip starting {old_start}. Also close out its linked task called '{existing_title}'.",
    ],
    [
        "Find the '{existing_title}' task linked to the {destination} trip starting {old_start} and move its due date to {new_date}.",
        "Reschedule the '{existing_title}' to-do for the {destination} trip beginning {old_start} to {new_date}.",
        "Look up the {destination} trip starting {old_start}, find its linked '{existing_title}' task, and change that task's deadline to {new_date}.",
        "The '{existing_title}' task for the {destination} trip starting {old_start} should be due {new_date}; find and update that task.",
    ],
    [
        "Create trip {new_trip_id} to {destination} starting {new_date}; then record completed task {new_task_id} titled '{new_title}' due {task_date}, linked to the new trip.",
        "Add a {destination} trip (ID {new_trip_id}, start {new_date}) and its linked, already completed to-do '{new_title}' (ID {new_task_id}, due {task_date}).",
        "Set up a new trip to {destination} on {new_date} with ID {new_trip_id}. Add linked task {new_task_id}, '{new_title}', due {task_date}, and mark it done.",
        "I need trip {new_trip_id} for {destination} on {new_date}, plus a completed task {new_task_id} named '{new_title}' due {task_date} on that trip.",
    ],
    [
        "Find the '{existing_title}' task linked to the {destination} trip starting {old_start} and mark it done.",
        "Complete the existing '{existing_title}' to-do for the {destination} trip beginning {old_start}. Look it up first.",
        "Locate the '{existing_title}' task linked to my {destination} trip starting {old_start} and change its status to done.",
        "The '{existing_title}' task for the {destination} trip starting {old_start} is finished; find it and record that status.",
    ],
    [
        "If the {destination} trip starting {old_start} is booked, cancel it and create task {new_task_id} titled '{new_title}' due {new_date}; otherwise make no changes.",
        "Check my {destination} trip beginning {old_start}. Only when it is booked, cancel it and add to-do {new_task_id}, '{new_title}', due {new_date}.",
        "Look up the {destination} trip starting {old_start}; if still booked, cancel it and create task '{new_title}' (ID {new_task_id}) due {new_date}. Leave a cancelled trip alone.",
        "For my {destination} trip beginning {old_start}, cancel it and make a follow-up task {new_task_id} named '{new_title}' due {new_date} only if it is currently booked.",
    ],
]

DESTINATIONS = ["Kyoto", "Oslo", "Lisbon", "Taipei"]


def opaque_id(kind: str, tag: str) -> str:
    return f"{kind}-{hashlib.sha256(f'{kind}:{tag}'.encode()).hexdigest()[:10]}"


def make_case(template: int, variant: int) -> dict:
    family, phrasing = divmod(template, 4)
    destination = DESTINATIONS[(template + variant) % len(DESTINATIONS)]
    tag = f"T{template:02d}V{variant}"
    old_trip_id = opaque_id("trip", tag)
    old_task_id = opaque_id("task", tag)
    other_trip_id = opaque_id("other-trip", tag)
    new_trip_id = f"new-trip-{tag}"
    new_task_id = f"new-task-{tag}"
    existing_title = f"Confirm {destination} booking"
    new_title = f"Review {destination} plans {tag}"
    new_date = f"2027-{(template % 9) + 1:02d}-{variant + 10:02d}"
    task_date = f"2027-{(template % 9) + 1:02d}-{variant + 12:02d}"
    old_start = f"2027-02-{variant + 10:02d}"
    other_start = f"2027-03-{variant + 15:02d}"
    target_status = "cancelled" if family == 5 and variant % 2 else "booked"
    trips = [
        {"id": old_trip_id, "destination": destination, "startDate": old_start, "status": target_status},
        {"id": other_trip_id, "destination": destination, "startDate": other_start, "status": "booked"},
        {"id": opaque_id("third-trip", tag), "destination": "Berlin", "startDate": "2027-04-02", "status": "booked"},
    ]
    tasks = [
        {"id": old_task_id, "title": existing_title, "dueDate": "2027-01-20", "status": "open", "tripID": old_trip_id},
        {"id": opaque_id("other-booking-task", tag), "title": existing_title, "dueDate": "2027-01-22", "status": "open", "tripID": other_trip_id},
        {"id": opaque_id("other-task", tag), "title": "Check passport", "dueDate": "2027-01-05", "status": "open", "tripID": None},
    ]
    expected_trips = [dict(item) for item in trips]
    expected_tasks = [dict(item) for item in tasks]
    if family == 0:
        expected_tasks.append({"id": new_task_id, "title": new_title, "dueDate": new_date, "status": "open", "tripID": old_trip_id})
        oracle = [("search_trips", {"destination": destination}),
                  ("create_task", {"task_id": new_task_id, "title": new_title, "due_date": new_date, "trip_id": old_trip_id})]
    elif family == 1:
        expected_trips[0]["status"] = "cancelled"
        expected_tasks[0]["status"] = "done"
        oracle = [("search_trips", {"destination": destination}),
                  ("set_trip_status", {"trip_id": old_trip_id, "status": "cancelled"}),
                  ("find_tasks", {"query": existing_title}),
                  ("set_task_status", {"task_id": old_task_id, "status": "done"})]
    elif family == 2:
        expected_tasks[0]["dueDate"] = new_date
        oracle = [("search_trips", {"destination": destination}),
                  ("find_tasks", {"query": existing_title}),
                  ("reschedule_task", {"task_id": old_task_id, "due_date": new_date})]
    elif family == 3:
        expected_trips.append({"id": new_trip_id, "destination": destination, "startDate": new_date, "status": "booked"})
        expected_tasks.append({"id": new_task_id, "title": new_title, "dueDate": task_date, "status": "done", "tripID": new_trip_id})
        oracle = [("add_trip", {"trip_id": new_trip_id, "destination": destination, "start_date": new_date}),
                  ("create_task", {"task_id": new_task_id, "title": new_title, "due_date": task_date, "trip_id": new_trip_id}),
                  ("set_task_status", {"task_id": new_task_id, "status": "done"})]
    elif family == 4:
        expected_tasks[0]["status"] = "done"
        oracle = [("search_trips", {"destination": destination}),
                  ("find_tasks", {"query": existing_title}),
                  ("set_task_status", {"task_id": old_task_id, "status": "done"})]
    elif family == 5:
        oracle = [("search_trips", {"destination": destination})]
        if target_status == "booked":
            expected_trips[0]["status"] = "cancelled"
            expected_tasks.append({"id": new_task_id, "title": new_title, "dueDate": new_date, "status": "open", "tripID": None})
            oracle += [("set_trip_status", {"trip_id": old_trip_id, "status": "cancelled"}),
                       ("create_task", {"task_id": new_task_id, "title": new_title, "due_date": new_date})]
    prompt = PHRASINGS[family][phrasing].format(**locals())
    return {
        "task_id": tag,
        "template_id": f"T{template:02d}",
        "family": family,
        # Hold out complete templates, including all four fixture variants.
        # One template per workflow family is development data.
        "split": "dev" if phrasing == 0 else "test",
        "prompt": prompt,
        "oracle_actions": [{"operation": operation, "arguments": arguments} for operation, arguments in oracle],
        "initial": {"trips": trips, "tasks": tasks},
        "expected": {"trips": expected_trips, "tasks": expected_tasks},
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    corpus = [make_case(template, variant) for template in range(24) for variant in range(4)]
    OUTPUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(corpus)} tasks to {OUTPUT}")


if __name__ == "__main__":
    main()
