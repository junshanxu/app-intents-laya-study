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

For the first system proof, create and check `AI_search_trips` and `AI_create_task` before constructing the remaining five. The read output must contain the fixture trip and the write must appear in `~/Library/Application Support/AppIntentsLayaStudy/tasks.json`. Run `python3 experiment/run.py gate` for this two-action proof, then `python3 experiment/run.py gate-all` for all seven wrappers.

For reproducible file-based setup, `python3 scripts/generate_shortcuts.py /tmp/study-unsigned` creates unsigned wrappers containing the same App Intent actions and parameter mappings. Sign each with `shortcuts sign --mode anyone --input INPUT --output OUTPUT`, then import it through the Shortcuts editor. [Apple says signing sends it a copy for validation](https://support.apple.com/en-gb/guide/shortcuts-mac/apd455c82f02/mac); these generated files contain only synthetic operation definitions and no credential. Importing a generated wrapper does not prove it works: run `python3 experiment/run.py gate-all` to verify all seven system calls and final-state effects.

Observed on this machine: the initial ad-hoc build was rejected by `linkd` with `requiresValidatedBundle`. After signing and reinstalling both apps with an Apple Development identity, all seven real Shortcuts action wrappers passed `gate-all` on 27 September 2026. An explicit **Stop and Output** action is required for reliable CLI output on this Mac.
