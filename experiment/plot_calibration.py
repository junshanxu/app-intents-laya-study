"""Plot observed Laya development-set decisions without test-set information."""
from __future__ import annotations

import json

import matplotlib.pyplot as plt

from state import ROOT


def main() -> None:
    calibration = json.loads((ROOT / "data/laya_dev_calibration.json").read_text())
    records = calibration["records"]
    thresholds = [index / 100 for index in range(101)]
    correct = [sum(row["correct"] and row["confidence"] >= value for row in records) for value in thresholds]
    wrong = [sum(not row["correct"] and row["confidence"] >= value for row in records) for value in thresholds]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.step(thresholds, correct, where="post", label="Correct accepted", color="#28748d", linewidth=2)
    ax.step(thresholds, wrong, where="post", label="Wrong accepted", color="#be5a39", linewidth=2)
    ax.set(xlabel="Minimum reported confidence", ylabel="Accepted development decisions",
           title=f"Zero-shot Laya on {len(records)} ideal development steps")
    ax.set_xlim(0, 1)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    output = ROOT / "figures"
    output.mkdir(exist_ok=True)
    fig.savefig(output / "laya_dev_calibration.png", dpi=180)
    fig.savefig(output / "laya_dev_calibration.pdf")
    print(f"Wrote {output / 'laya_dev_calibration.png'} and PDF")


if __name__ == "__main__":
    main()
