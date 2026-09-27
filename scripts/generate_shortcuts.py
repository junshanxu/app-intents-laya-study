"""Generate unsigned Shortcuts wrappers for the study's signed App Intents.

Sign each result with ``shortcuts sign --mode anyone`` and import it into
Shortcuts. The study gate checks the actual Shortcuts execution path afterward.
"""
from __future__ import annotations

import argparse
import plistlib
import uuid
from pathlib import Path


INPUT_CLASSES = [
    "WFAppContentItem", "WFAppStoreAppContentItem", "WFArticleContentItem",
    "WFContactContentItem", "WFDateContentItem", "WFEmailAddressContentItem",
    "WFFolderContentItem", "WFGenericFileContentItem", "WFImageContentItem",
    "WFiTunesProductContentItem", "WFLocationContentItem", "WFDCMapsLinkContentItem",
    "WFAVAssetContentItem", "WFPDFContentItem", "WFPhoneNumberContentItem",
    "WFRichTextContentItem", "WFSafariWebPageContentItem", "WFStringContentItem",
    "WFURLContentItem",
]

# Shortcut name: (bundle suffix, Intent type, visible output name, Swift parameter -> JSON key)
WRAPPERS = {
    "AI_search_trips": ("trips", "SearchTripsIntent", "Study: Search Trips", {"destination": "destination"}),
    "AI_add_trip": ("trips", "AddTripIntent", "Study: Add Trip", {"tripID": "trip_id", "destination": "destination", "startDate": "start_date"}),
    "AI_set_trip_status": ("trips", "SetTripStatusIntent", "Study: Set Trip Status", {"tripID": "trip_id", "status": "status"}),
    "AI_find_tasks": ("tasks", "FindTasksIntent", "Study: Find Tasks", {"query": "query"}),
    "AI_create_task": ("tasks", "CreateTaskIntent", "Study: Create Task", {"taskID": "task_id", "title": "title", "dueDate": "due_date", "tripID": "trip_id"}),
    "AI_set_task_status": ("tasks", "SetTaskStatusIntent", "Study: Set Task Status", {"taskID": "task_id", "status": "status"}),
    "AI_reschedule_task": ("tasks", "RescheduleTaskIntent", "Study: Reschedule Task", {"taskID": "task_id", "dueDate": "due_date"}),
}


def input_variable(key: str) -> dict:
    return {
        "WFSerializationType": "WFTextTokenString",
        "Value": {"string": "\ufffc", "attachmentsByRange": {"{0, 1}": {
            "Type": "ExtensionInput",
            "Aggrandizements": [
                {"Type": "WFCoercionVariableAggrandizement", "CoercionItemClass": "WFDictionaryContentItem"},
                {"Type": "WFDictionaryValueVariableAggrandizement", "DictionaryKey": key},
            ],
        }}},
    }


def workflow(name: str) -> dict:
    bundle, intent, output_name, params = WRAPPERS[name]
    action_uuid = str(uuid.uuid4()).upper()
    output_uuid = str(uuid.uuid4()).upper()
    action_params = {
        "AppIntentDescriptor": {
            "BundleIdentifier": f"tech.xj3.appintentstudy.{bundle}",
            "Name": "TripLedger" if bundle == "trips" else "TaskBoard",
            "AppIntentIdentifier": intent,
        },
        "UUID": action_uuid,
    }
    action_params.update({swift_name: input_variable(key) for swift_name, key in params.items()})
    return {
        "WFWorkflowActions": [
            {"WFWorkflowActionIdentifier": f"tech.xj3.appintentstudy.{bundle}.{intent}",
             "WFWorkflowActionParameters": action_params},
            {"WFWorkflowActionIdentifier": "is.workflow.actions.output",
             "WFWorkflowActionParameters": {
                 "WFOutput": {"WFSerializationType": "WFTextTokenString", "Value": {
                     "string": "\ufffc", "attachmentsByRange": {"{0, 1}": {
                         "Type": "ActionOutput", "OutputUUID": action_uuid, "OutputName": output_name,
                     }}}},
                 "UUID": output_uuid,
             }},
        ],
        "WFWorkflowClientVersion": "5111.0.1",
        "WFWorkflowMinimumClientVersion": "900",
        "WFWorkflowTypes": ["NCWidget"],
        "WFWorkflowInputContentItemClasses": INPUT_CLASSES,
        "WFWorkflowOutputContentItemClasses": ["WFStringContentItem"],
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4274264319, "WFWorkflowIconGlyphNumber": 61440},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("names", nargs="*", choices=sorted(WRAPPERS))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name in args.names or WRAPPERS:
        (args.output_dir / f"{name}.shortcut").write_bytes(plistlib.dumps(workflow(name), fmt=plistlib.FMT_BINARY))
        print(name)


if __name__ == "__main__":
    main()
