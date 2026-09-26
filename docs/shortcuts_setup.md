# Custom Shortcuts wrappers

Create these shortcuts in the macOS Shortcuts editor. Their names are used literally by the bridge:

| Shortcut name | App Intent action | JSON input keys |
| --- | --- | --- |
| `AI_search_trips` | Study: Search Trips | `destination` |
| `AI_add_trip` | Study: Add Trip | `trip_id`, `destination`, `start_date` |
| `AI_set_trip_status` | Study: Set Trip Status | `trip_id`, `status` |
| `AI_find_tasks` | Study: Find Tasks | `query` |
| `AI_create_task` | Study: Create Task | `task_id`, `title`, `due_date`, optional `trip_id` |
| `AI_set_task_status` | Study: Set Task Status | `task_id`, `status` |
| `AI_reschedule_task` | Study: Reschedule Task | `task_id`, `due_date` |

Each wrapper receives a JSON file through `shortcuts run NAME -i input.json`. In the editor, insert the **Shortcut Input** special variable into each App Intent parameter. Open the variable settings, set its type to **Dictionary**, then choose **Get Value for Key** and enter the corresponding JSON key from the table. Click outside the settings popover to commit the key. Add **Stop and Output** after the App Intent, with its result as the output. Verify that `shortcuts run NAME -i input.json -o output.txt` writes the return value. Do not use a Run Shell Script action or call the shared Swift service directly in these wrappers.

For the first system proof, create and check `AI_search_trips` and `AI_create_task` before constructing the remaining five. The read output must contain the fixture trip and the write must appear in `~/Library/Application Support/AppIntentsLayaStudy/tasks.json`. The complete gate is implemented in `experiment/run.py gate`.

Current diagnostic: Shortcuts discovered the actions, but `linkd` rejected the ad-hoc signed app with `requiresValidatedBundle`. Sign and reinstall with a real Apple development identity before continuing. On this macOS installation, a pure Text shortcut hung at the CLI until an explicit **Stop and Output** action was added; with that action, the CLI returned `smoke-ok` successfully.
