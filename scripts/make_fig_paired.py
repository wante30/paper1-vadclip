"""Figure: paired per-seed comparisons (reads evidence/results_ledger.csv only).

Each panel connects the two arms of one seed. Panels:
  UCF AUC1  B0 -> Ours      XD AP2  B0 -> Ours
  UCF AUC1  post -> pre     XD AP2  C (lambda=0) -> Stage 2
Writes paper/figures/fig_paired.pdf.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ("234", "235", "236")
# Okabe-Ito colours (colour-blind safe) plus distinct markers per seed
STYLE = {"234": ("#0072B2", "o"), "235": ("#D55E00", "s"), "236": ("#009E73", "^")}

with (ROOT / "evidence" / "results_ledger.csv").open(encoding="utf-8") as f:
    L = {(r["dataset"], r["protocol"], r["condition"], r["seed"], r["metric"]): float(r["value"]) * 100
         for r in csv.DictReader(f)}

PANELS = [
    ("UCF-Crime", "UCF", "AUC1", "AUC (%)", ("B0", "VadCLIP"), ("Final", "Ours")),
    ("XD-Violence", "XD", "AP2", "AP (%)", ("B0", "VadCLIP"), ("T", "Ours")),
    ("UCF-Crime, Stage 1", "UCF", "AUC1", "AUC (%)", ("POST", "post-agg."), ("AE", "pre-agg.")),
    ("XD-Violence, Stage 2", "XD", "AP2", "AP (%)", ("C", r"$\lambda=0$"), ("T", "Stage 2")),
]


def main():
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 1.9))
    for ax, (title, ds, m, ylabel, (ca, la), (cb, lb)) in zip(axes, PANELS):
        deltas = []
        for s in SEEDS:
            a, b = L[(ds, "clean", ca, s, m)], L[(ds, "clean", cb, s, m)]
            deltas.append(b - a)
            color, marker = STYLE[s]
            ax.plot([0, 1], [a, b], color=color, marker=marker, markersize=4, linewidth=1.2,
                    label=f"seed {s}")
        mean = sum(deltas) / len(deltas)
        pos = sum(d > 0 for d in deltas)
        ax.set_xticks([0, 1], [la, lb])
        ax.set_xlim(-0.3, 1.3)
        ax.set_title(f"{title}\n$\\Delta$ = {mean:+.2f} ({pos}/{len(deltas)})", fontsize=8)
        ax.set_ylabel(ylabel)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=7,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(w_pad=1.0, rect=(0, 0.08, 1, 1))
    out = ROOT / "paper" / "figures" / "fig_paired.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main()
