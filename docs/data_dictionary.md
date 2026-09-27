# Released data fields

`data/tasks.json` contains synthetic initial and expected application states, the user task text, a template ID, a fixture ID, and an ideal trajectory used only for corpus verification. Ideal trajectories are not passed to the agent.

After the experiment, `data/results_public.jsonl` contains one record per agent run. `task_id`, `template_id`, `split`, `repeat`, `backend`, and `decision` identify a matched unit and one of the four arms. `run_id` is a deterministic combination of those fields.

- `success`: exact equality between the final application state and the expected state, after normalizing an absent optional trip link to JSON null.
- `mismatched_fields`: count of missing, unexpected, or unequal record fields in the final state.
- `extra_changes`: count of record additions or field changes beyond the expected task effect.
- `invalid_calls`: number of application tool calls rejected or failed at the MCP bridge or underlying operation.
- `failure_recovery`: true when a run contains a failed application call yet reaches the exact expected final state.
- `tool_calls`: application action calls, including failed calls and reads; `laya_calls`: consultation calls.
- `app_latency_ms`: sum of application action execution times; `laya_latency_ms`: sum of local decision consultations; `tool_latency_ms`: sum of both; `total_latency_ms`: wall time for the Claude Code process.
- `model_usage`: token counts reported by the Claude Code process, when present. Missing fields indicate unavailable reporting rather than zero use.
- `model_turns`, `timeout`, `process_ok`, `exit_code`: execution diagnostics. A successful process is not sufficient for `success`.

Raw tool traces and final-state snapshots remain in ignored `data/runs/`. The public export deliberately omits tool arguments, model conversation text, local paths, and environment variables. It includes no real travel or to-do data.
