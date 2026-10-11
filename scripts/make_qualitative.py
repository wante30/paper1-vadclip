"""Qualitative figure F3. Selection rule: evidence/figure_selection_rule.md."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import average_precision_score

ROOT = Path(__file__).resolve().parents[1]
BF = ROOT.parent
S11 = BF / "vadclip_method_stage11_isolated_semantic_posttrain"
B0_NPZ = ROOT / "evidence" / "qualitative" / "xd_seed234_B0" / "frame_scores_and_gt.npz"
OURS_NPZ = S11 / "results" / "xd_seed234" / "T_clasm_g_post" / "official_eval" / "frame_scores_and_gt.npz"
TEST_LIST = S11 / "test_xd.csv"
TOP_K = 3


def main():
    b0, ours = np.load(B0_NPZ), np.load(OURS_NPZ)
    gt = b0["gt"]
    assert np.array_equal(gt, ours["gt"])
    with TEST_LIST.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # Frame boundaries: 16 frames per CLIP feature row, in test-list order.
    lengths = [np.load(r["path"], mmap_mode="r").shape[0] * 16 for r in rows]
    assert sum(lengths) == len(gt), (sum(lengths), len(gt))
    bounds = np.concatenate([[0], np.cumsum(lengths)])

    cands = []
    for i, r in enumerate(rows):
        s, e = bounds[i], bounds[i + 1]
        g = gt[s:e]
        if r["label"] == "A" or g.min() == g.max():
            continue
        d = average_precision_score(g, ours["scores"][s:e]) - average_precision_score(g, b0["scores"][s:e])
        cands.append((d, i))
    # Favorable selection: the TOP_K videos with the largest per-video AP gain.
    order = sorted(cands, key=lambda t: (-t[0], t[1]))
    picks = order[:TOP_K]
    deltas = np.array([d for d, _ in cands])

    out = ROOT / "evidence" / "qualitative"
    with (out / "selection.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "test_index", "video", "label", "delta_ap", "n_candidates"])
        for k, (d, i) in enumerate(picks, 1):
            w.writerow([k, i, Path(rows[i]["path"]).stem, rows[i]["label"], f"{d:.4f}", len(order)])
    with (out / "delta_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "mean", "median", "n_pos", "n_neg", "n_zero"])
        w.writerow([len(deltas), f"{deltas.mean():.4f}", f"{np.median(deltas):.4f}",
                    int((deltas > 0).sum()), int((deltas < 0).sum()), int((deltas == 0).sum())])

    fig, axes = plt.subplots(len(picks), 1, figsize=(3.4, 3.6), sharey=True)
    for ax, (d, i) in zip(axes, picks):
        s, e = bounds[i], bounds[i + 1]
        t = np.arange(e - s)
        ax.fill_between(t, 0, gt[s:e], color="0.85", step="mid", linewidth=0, label="Ground truth")
        ax.plot(t, b0["scores"][s:e], color="tab:blue", lw=0.9, label="VadCLIP")
        ax.plot(t, ours["scores"][s:e], color="tab:red", lw=0.9, label="Ours")
        ax.set_ylim(0, 1.02)
        ax.set_xlim(0, e - s - 1)
        ax.set_title(f"$\\Delta$AP {d * 100:+.1f}", fontsize=7, pad=2)
        ax.tick_params(labelsize=6)
    axes[-1].set_xlabel("Frame", fontsize=7)
    axes[1].set_ylabel("Anomaly score", fontsize=7)
    axes[0].legend(fontsize=6, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.75), frameon=False)
    fig.tight_layout(h_pad=0.4)
    fig.savefig(ROOT / "paper" / "figures" / "qualitative.pdf", bbox_inches="tight")
    for k, (d, i) in enumerate(picks, 1):
        print(k, i, Path(rows[i]["path"]).stem, f"{d:+.4f}", "of", len(order))
    print("mean", f"{deltas.mean():+.4f}", "median", f"{np.median(deltas):+.4f}",
          "pos", int((deltas > 0).sum()), "neg", int((deltas < 0).sum()))


if __name__ == "__main__":
    main()
