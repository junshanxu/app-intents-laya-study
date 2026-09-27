"""Render descriptive figures from the locked primary analysis."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"


def save(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.png", dpi=200, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    report = json.loads((ROOT / "data/analysis.json").read_text())
    labels = ["App Intents vs CLI", "Laya consultation vs Claude", "Factor interaction"]
    fields = ["interface_difference", "laya_difference", "interaction"]
    point = [100 * report["success"][field] for field in fields]
    limits = [[100 * v for v in report["ci_95_template_bootstrap"][field]] for field in fields]
    fig, ax = plt.subplots(figsize=(7.3, 3.3))
    y = [2, 1, 0]
    ax.axvline(0, color="#555555", linewidth=1)
    for index, position in enumerate(y):
        ax.plot(limits[index], [position, position], color="#256eaa", linewidth=2)
        ax.plot([limits[index][0], limits[index][0]], [position - .08, position + .08], color="#256eaa")
        ax.plot([limits[index][1], limits[index][1]], [position - .08, position + .08], color="#256eaa")
        ax.scatter(point[index], position, s=45, color="#123c66", zorder=3)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Paired success difference (percentage points)")
    ax.set_title("Primary effects with 95% template-bootstrap intervals")
    ax.set_ylim(-.5, 2.5)
    ax.grid(axis="x", alpha=.2)
    save(fig, "paired_effects")

    ancillary = report["ancillary_means"]
    arms = ["intents_claude", "intents_laya", "cli_claude", "cli_laya"]
    names = ["Intents + Claude", "Intents + Laya", "CLI + Claude", "CLI + Laya"]
    colors = ["#3974aa", "#75a9c9", "#d18b40", "#e3b77c"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.7))
    x = range(4)
    axes[0].bar(x, [ancillary[arm]["invalid_calls"] for arm in arms], color=colors)
    axes[0].set_ylabel("Invalid application calls per run")
    axes[0].set_title("Tool-call errors (descriptive)")
    axes[1].bar(x, [ancillary[arm]["total_latency_ms"] / 1000 for arm in arms], color=colors)
    axes[1].set_ylabel("Mean Claude process time (s)")
    axes[1].set_title("Wall time (descriptive)")
    for ax in axes:
        ax.set_xticks(list(x), names, rotation=20, ha="right")
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "secondary_metrics")
    print(f"Wrote paired-effects and secondary-metrics figures to {FIGURES}")


if __name__ == "__main__":
    main()
