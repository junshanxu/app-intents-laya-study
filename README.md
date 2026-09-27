# macOS App Intents × Laya Agent Study

This repository contains a controlled, synthetic study of macOS App Intents versus a command-line interface for Claude Code agents, with and without a local Laya next-action gate. The two SwiftUI apps are **Study Trips** and **Study Tasks**. They share the exact same `StudyService` methods with the `studyctl` CLI. No real travel or task data is used.

## Current status

- Both apps now build with an Apple Development identity, pass strict signature verification, and are installed under `~/Applications/AppIntentsLayaStudy`. Shortcuts discovers their App Intent actions.
- `studyctl`, the MCP bridge, 96 deterministic tasks, independent final-state scoring, Laya development calibration, and analysis scripts are implemented. All 96 authored action trajectories reproduce their expected final state through the Swift CLI.
- **All seven Shortcuts wrappers passed the system gate on 27 September 2026.** The gate exercised each action through `shortcuts run` and verified the resulting application state. The revised corpus completed all 96 development-arm runs and all 864 held-out runs. The held-out exact-state scores were 200, 202, 201, and 202 successes out of 216 for Intents + Claude, Intents + Laya consultation, CLI + Claude, and CLI + Laya consultation, respectively. The paired interface difference was −0.23 percentage points (95% template-bootstrap interval −1.62 to +1.16). An earlier easier corpus produced 65/65 successful pilot runs and was replaced before any held-out run.
- The local multilingual Laya service works when the request explicitly selects `model="multilingual"`. On the template-isolated development set it selected 18 of 68 ideal next steps correctly. The conservative, development-only threshold is 1.01, which delegates all steps to Claude. [The development calibration chart](figures/laya_dev_calibration.png) is an observed result; it is not evidence of a benefit on held-out tasks.

## Build and sign

Requirements: macOS, Xcode, XcodeGen, Swift 6, Claude Code CLI, Python 3 with Matplotlib for analysis, and a validated Apple development signing identity. Apple says macOS apps using certain system services require signing. Ad-hoc signing is insufficient on this machine for App Intents execution through Shortcuts.

```bash
cd /path/to/app-intents-laya-study
zsh scripts/build-cli.sh
APPLE_DEVELOPMENT_TEAM=YOUR_TEAM_ID zsh scripts/build-apps.sh
```

The second script refuses an ad-hoc build, installs both apps under `~/Applications/AppIntentsLayaStudy`, and registers them with Launch Services. Start each app once, then create or import seven custom Shortcuts wrappers described in [docs/shortcuts_setup.md](docs/shortcuts_setup.md). Apple's App Shortcuts feature is not available on macOS; the experiment uses custom Shortcuts that call App Intent actions.

## Synthetic data and protocol

```bash
python3 experiment/generate_tasks.py
zsh scripts/build-cli.sh
python3 experiment/verify_corpus.py
```

`data/tasks.json` contains 24 templates × 4 resettable fixtures. Six complete templates, one per workflow family, form development data (24 tasks); the other 18 complete templates form held-out test data (72 tasks). The test set runs in four paired arms with three repeats (864 agent runs). `experiment/state.py` resets app JSON state and grades the final state without consulting the agent transcript. A result is successful only when the complete final state equals the expected state. Extra changes, invalid calls, tool count, failure recovery, use, and latency are also recorded.

The App Intents arm exposes seven typed MCP tools backed only by `shortcuts run`. The CLI arm exposes a single command tool that parses `studyctl OPERATION JSON_ARGUMENTS` without invoking a shell. Both reach the same Swift service. The Laya arms require the agent to call `recommend_action` before each application action. A suggestion above the development-locked threshold constrains the next action; below it, Claude plans. Jev implements the same conceptual decision interface but is excluded until credentials exist.

## Local Laya and formal run

Start the existing local server with the multilingual checkpoint:

```bash
HF_HUB_OFFLINE=1 /path/to/laya-local-deploy/start.sh
python3 experiment/calibrate_laya.py
python3 experiment/run.py gate-all
```

The gate runs all seven operations through Shortcuts and verifies the final app state. It will not call Swift `perform()` directly or silently use the CLI fallback. If Laya is installed elsewhere, set `STUDY_LAYA_PYTHON` to that environment's Python executable before formal runs. The local endpoint defaults to `http://127.0.0.1:8765/v1/systemone` and can be set with `STUDY_LAYA_URL`. `STUDY_LAYA_CACHE_REF` can point to the local Hugging Face revision file when the cache is in a nonstandard location.

Only after the gate passes, provide a Coding Plan key to the experiment process. The script sets the official Anthropic-compatible Coding Plan base URL, fixes `doubao-seed-2.1-pro`, and ignores the user's global Claude Code settings. Do not put the key in this repository, logs, or a shell history file. In an interactive zsh session, enter it without echo and remove it after the runs:

```bash
read -rs "ARK_CODING_PLAN_API_KEY?Coding Plan key: "
export ARK_CODING_PLAN_API_KEY
python3 experiment/run.py dev
python3 experiment/run.py test
unset ARK_CODING_PLAN_API_KEY
python3 experiment/analyze.py
```

The script does not print or write the key. It locks macOS, Xcode, Claude Code, Laya, model, base URL, the corpus, calibration, and implementation hashes before test runs. Results live under ignored `data/runs/` until reviewed and stripped of any environment-specific information for release. A stopped run resumes by skipping completed arm–task–repetition combinations.

## Analysis and constraints

`experiment/analyze.py` requires all 216 complete paired test replicates. It estimates the App Intents effect, Laya consultation effect, and interaction, with 95% percentile intervals bootstrapped by the 18 held-out task templates. Results are in [analysis.json](data/analysis.json), with [success](figures/success_rates.png), [paired-effect](figures/paired_effects.png), and [secondary-outcome](figures/secondary_metrics.png) figures. The [English draft](paper/draft.md) reports the observed results and limitations.

After all runs finish, `python3 experiment/export_public.py` creates `data/results_public.jsonl` from a fixed allowlist of synthetic task IDs, outcomes, usage counts, and timings. Raw tool traces and final-state snapshots stay in ignored `data/runs/`; the public file contains no conversation text, absolute paths, or credentials. The exporter requires the complete development and test run counts, and refuses duplicate run IDs.
See the [data dictionary](docs/data_dictionary.md) for field definitions.

`python3 experiment/robustness.py` reproduces the clearly **post hoc** sensitivity audit in [robustness.json](data/robustness.json). Fifty-eight of 59 exact-state failures differ only in whether a new follow-up task is linked to its target trip; the prompt did not specify that optional field. Accepting either link choice yields 863/864 task successes. The original exact-state outcome remains primary, but this ambiguity and the resulting ceiling mean the current benchmark is not sufficient to claim a task-completion advantage or submit the paper without revision. The Laya threshold accepted zero of 1,079 held-out consultations, so the Laya arms measure consultation overhead and prompting rather than Laya's action selection.

This small synthetic benchmark cannot establish performance on arbitrary Mac apps or prove that Apple's schema alone caused an effect. The App Intents contrast includes Shortcuts runtime and bridge overhead. Because zero-shot Laya's development accuracy is poor, further work may require domain fine-tuning and a new, separately held-out evaluation; changing the threshold after test results would invalidate the present comparison.

## Primary references

- [Apple App Intents documentation](https://developer.apple.com/documentation/appintents/app-intents)
- [Apple Shortcuts command-line guide](https://support.apple.com/en-euro/guide/shortcuts-mac/-apd455c82f02/mac)
- [Apple App Shortcuts platform guidance](https://developer.apple.com/design/human-interface-guidelines/app-shortcuts)
- [Laya model card](https://huggingface.co/convaiinnovations/laya)
- [Volcano Ark Coding Plan quick start](https://docs.volcengine.com/docs/ark/coding-plan-personal-get-started?lang=zh)
- [ShortcutsBench](https://arxiv.org/abs/2407.00132)
- [MacArena](https://arxiv.org/abs/2606.06560)
- [MacAgentBench](https://arxiv.org/abs/2606.22557)
