"""Paired, template-clustered effect estimates and publication chart."""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data/runs/results.jsonl"
OUTPUT = ROOT / "data/analysis.json"
FIGURE = ROOT / "figures/success_rates.png"
RNG = random.Random(20260926)
ARMS = [("intents", "claude"), ("intents", "laya"), ("cli", "claude"), ("cli", "laya")]


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def main() -> None:
    if not RESULTS.exists():
        raise SystemExit("No formal results yet; run the Shortcuts gate and experiment first")
    rows = [json.loads(line) for line in RESULTS.read_text().splitlines()]
    rows = [row for row in rows if row["split"] == "test"]
    by_pair = defaultdict(dict)
    for row in rows:
        key = (row["task_id"], row["repeat"])
        arm = (row["backend"], row["decision"])
        if arm in by_pair[key]:
            raise ValueError(f"Duplicate run for {key} {arm}")
        by_pair[key][arm] = row
    complete = {key: arms for key, arms in by_pair.items() if set(arms) == set(ARMS)}
    if len(complete) != 72 * 3:
        raise SystemExit(f"Need 216 complete paired test replicates; have {len(complete)}")
    templates = sorted({arms[ARMS[0]]["template_id"] for arms in complete.values()})
    if len(templates) != 18:
        raise SystemExit(f"Need 18 test templates; have {len(templates)}")

    def estimates(keys: list[tuple]) -> dict:
        group = {f"{arm[0]}_{arm[1]}": mean([float(complete[key][arm]["success"]) for key in keys]) for arm in ARMS}
        interface = mean([(
            float(complete[key][("intents", "claude")]["success"]) +
            float(complete[key][("intents", "laya")]["success"]) -
            float(complete[key][("cli", "claude")]["success"]) -
            float(complete[key][("cli", "laya")]["success"])) / 2 for key in keys])
        decision = mean([(
            float(complete[key][("intents", "laya")]["success"]) +
            float(complete[key][("cli", "laya")]["success"]) -
            float(complete[key][("intents", "claude")]["success"]) -
            float(complete[key][("cli", "claude")]["success"])) / 2 for key in keys])
        interaction = mean([(
            float(complete[key][("intents", "laya")]["success"]) -
            float(complete[key][("intents", "claude")]["success"]) -
            float(complete[key][("cli", "laya")]["success"]) +
            float(complete[key][("cli", "claude")]["success"])) for key in keys])
        return {"groups": group, "interface_difference": interface,
                "laya_difference": decision, "interaction": interaction}

    point = estimates(list(complete))
    by_template = defaultdict(list)
    for key, arms in complete.items():
        by_template[arms[ARMS[0]]["template_id"]].append(key)
    samples = []
    for _ in range(5000):
        drawn = [RNG.choice(templates) for _ in templates]
        keys = [key for template in drawn for key in by_template[template]]
        samples.append(estimates(keys))
    ci = {}
    for metric in ("interface_difference", "laya_difference", "interaction"):
        ci[metric] = [percentile([sample[metric] for sample in samples], 0.025),
                      percentile([sample[metric] for sample in samples], 0.975)]
    for arm in point["groups"]:
        ci[arm] = [percentile([sample["groups"][arm] for sample in samples], 0.025),
                   percentile([sample["groups"][arm] for sample in samples], 0.975)]
    ancillary = {}
    for arm in ARMS:
        label = f"{arm[0]}_{arm[1]}"
        group_rows = [arms[arm] for arms in complete.values()]
        ancillary[label] = {metric: mean([float(row[metric]) for row in group_rows]) for metric in
                            ("invalid_calls", "extra_changes", "mismatched_fields", "tool_calls", "app_latency_ms",
                             "laya_latency_ms", "tool_latency_ms", "total_latency_ms")}
        ancillary[label]["failure_recovery_rate"] = mean([float(row["failure_recovery"]) for row in group_rows])
        ancillary[label]["usage_reported_rate"] = mean([bool(row.get("model_usage")) for row in group_rows])
        for field in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            available = [row["model_usage"][field] for row in group_rows if field in row.get("model_usage", {})]
            ancillary[label][f"mean_{field}"] = mean(available) if available else None
    report = {"n_paired_replicates": len(complete), "n_templates": len(templates),
              "success": point, "ci_95_template_bootstrap": ci,
              "ancillary_means": ancillary,
              "method": "5000 percentile bootstrap resamples of 18 held-out templates; all paired repetitions retained within a resampled template"}
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    labels = ["Intents + Claude", "Intents + Laya", "CLI + Claude", "CLI + Laya"]
    values = [point["groups"][f"{a}_{b}"] for a, b in ARMS]
    errors = [[values[i] - ci[f"{a}_{b}"][0] for i, (a, b) in enumerate(ARMS)],
              [ci[f"{a}_{b}"][1] - values[i] for i, (a, b) in enumerate(ARMS)]]
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    ax.bar(labels, values, yerr=errors, capsize=4, color=["#3974aa", "#75a9c9", "#d18b40", "#e3b77c"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Task success rate")
    ax.set_title("Synthetic macOS tasks: final-state success")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    FIGURE.parent.mkdir(exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    print(f"Wrote {OUTPUT} and {FIGURE}")


if __name__ == "__main__":
    main()
