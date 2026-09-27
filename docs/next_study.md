# Next study: from integration result to a submit-ready comparison

The completed 864-run experiment is a feasibility and measurement study. It does not establish that App Intents improve task completion: the paired exact-state interface estimate is −0.23 percentage points with a 95% interval from −1.62 to +1.16, and 58 of 59 failures are an ambiguous optional trip link. Laya accepted no next-action suggestions. The following is a **new protocol proposal**, not a reinterpretation of the held-out results.

## Repair the task and verifier contract

1. Write explicit constraints for every optional field. Some tasks should say "link this task to the trip"; others should say "leave the task unlinked". A third category can deliberately leave the link unspecified, with both states accepted by a semantic verifier.
2. Define each task's required predicates and forbidden side effects independently of a single authored action trajectory. Keep full-state equality as an additional strict diagnostic.
3. Have two reviewers independently annotate at least a sample of prompts and expected predicates before running agents. Resolve disagreements without seeing agent outcomes.
4. Keep the current 72 test fixtures retired for model or threshold selection. Generate new held-out templates after the benchmark and decision layer are frozen.

## Separate tool presentation from execution path

The present Intents arm exposes seven named MCP tools and executes through Shortcuts; the CLI arm exposes one command tool and executes through `studyctl`. A follow-up should cross these factors: seven named tools versus one command tool, and Shortcuts/App Intents versus the Swift CLI backend. This 2 × 2 design would estimate whether fewer invalid calls come from the agent-visible schema, the native system path, or their interaction. Every backend must still reach the same `StudyService` and be verified against final state. Retain the real `shortcuts run` system gate for the native path.

## Make failures consequential and diverse

Add more synthetic apps and action types: date changes, multi-step dependencies, cross-app references, reversible edits, and no-op conditional branches. Some tasks should have tight action budgets or irreversible-looking synthetic side effects so a rejected call or wrong status cannot always be recovered without cost. Include explicit negative controls where the requested action is impossible. Select task templates using a development set only, then freeze a larger test population spanning difficulty levels rather than relying on many repeats of a few easy templates.

## Rebuild the Laya comparison

Zero-shot Laya selected 18/68 ideal development steps and sometimes assigned confidence 1.0 to wrong actions, forcing a threshold of 1.01 and zero accepted test recommendations. A useful second study needs an app-action-specific decision representation and, if permitted by the model's terms, fine-tuning or calibration on **new development data**. Fix the threshold on a separate validation split and report coverage, selective accuracy, wrong forced actions, and end-task effect. Compare against a prompt-only consultation control so any gain can be attributed to accepted Laya choices. Jev can later implement the same decision interface, but requires its own access and a separately frozen evaluation.

## Submission criterion

Before claiming a task-success advantage, require a semantic verifier with resolved annotation disagreements, non-ceiling tasks across multiple apps, an untouched test set, and a predeclared minimum useful effect (for example, five percentage points) that the confidence interval can distinguish from zero. Failure analyses should survive reasonable scoring alternatives. The current invalid-call reduction is a useful hypothesis, but it needs the crossed tool/backend study above to identify its mechanism.
