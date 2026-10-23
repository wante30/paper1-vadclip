"""Select median-near positive examples from EXISTING predictions; no inference.

Run from any working directory. Inputs are read-only. See the generated selection
report for the conditional-selection limitation and the complete source audit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
import numpy as np
import sklearn
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
BF = ROOT.parent
S2 = BF / "vadclip_method_stage2"
S11 = BF / "vadclip_method_stage11_isolated_semantic_posttrain"
SEED = 234  # Smallest seed in the matched experiment; never chosen by results.
EPS = 1e-12  # Only a floating-point zero tolerance, not an effect-size filter.
RULE = "all-candidate-middle-50pct-nearest-median-positive-v1"
STEM = "qualitative_representative"
CAPTION = (
    "Frame-level anomaly scores on UCF-Crime and XD-Violence for fixed, "
    "median-near positive-AP examples (matched seed 234). Shading denotes "
    "ground-truth abnormal segments. The selected curves remain similar; "
    "positive per-video AP differences do not imply reduced normal-region activation."
)
CONFIGS = [
    dict(dataset="UCF", title="UCF-Crime", condition="Final", n_videos=290,
         baseline=S2 / "results/seed234/granularity/B0_E2_clean",
         ours=S11 / "results/ucf_seed234/T_isolated_g_post/official_eval",
         test_list=S11 / "assets/ucf/ucf_test.csv", score_key="frame_scores_prob1",
         gt_key="ground_truth", ap_metric="AP1", auc_metric="AUC1"),
    dict(dataset="XD", title="XD-Violence", condition="T", n_videos=800,
         baseline=S2 / "results_xd/seed234/B0_clean/official_eval",
         ours=S11 / "results/xd_seed234/T_clasm_g_post/official_eval",
         test_list=S11 / "test_xd.csv", score_key="scores", gt_key="gt",
         ap_metric="AP2", auc_metric="AUC2"),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def segments(gt):
    """Zero-based half-open frame intervals [start, end)."""
    transitions = np.diff(np.r_[0, gt, 0].astype(np.int8))
    return list(zip(np.flatnonzero(transitions == 1).tolist(),
                    np.flatnonzero(transitions == -1).tolist()))


def select(rows):
    """Rank ALL mixed-GT candidates, not just the positive subset."""
    candidates = sorted((r for r in rows if r["eligible"]),
                        key=lambda r: (r["delta_ap"], r["test_index"]))
    require(bool(candidates), "No video contains both GT classes")
    n = len(candidates)
    midpoint = (n + 1) / 2
    for rank, row in enumerate(candidates, 1):
        row["rank_all_candidates"] = rank
        row["rank_fraction"] = (rank - 1) / (n - 1) if n > 1 else 0.5
        row["in_middle_50pct"] = 0.25 <= row["rank_fraction"] <= 0.75
    positives = [r for r in candidates if r["delta_ap"] > EPS]
    require(bool(positives), "No positive example: do not substitute a negative one")
    middle = [r for r in positives if r["in_middle_50pct"]]
    if middle:
        pick = min(middle, key=lambda r: (abs(r["rank_all_candidates"] - midpoint),
                                         r["delta_ap"], r["test_index"]))
        reason = "positive_in_middle_50pct_nearest_median_rank"
    else:
        pick = min(positives, key=lambda r: (r["delta_ap"], r["test_index"]))
        reason = "fallback_smallest_positive_no_central_positive"
    pick["selected"] = True
    pick["selection_reason"] = reason
    values = np.array([r["delta_ap"] for r in candidates])
    summary = dict(n_test=len(rows), n_candidates=n, n_positive=len(positives),
                   n_negative=int((values < -EPS).sum()),
                   n_zero=int((np.abs(values) <= EPS).sum()),
                   median_delta_ap=float(np.median(values)),
                   mean_delta_ap=float(values.mean()),
                   min_delta_ap=float(values.min()), max_delta_ap=float(values.max()),
                   target_median_rank=midpoint, selection_reason=reason)
    return pick, summary


def load_dataset(cfg, ledger, inputs):
    test_rows = read_csv(cfg["test_list"])
    inputs.add(cfg["test_list"])
    require(len(test_rows) == cfg["n_videos"], "Unexpected test-list size")
    names = [Path(r["path"]).stem for r in test_rows]
    require(len(set(names)) == len(names), "Duplicate video names")
    # Read existing feature headers only; never run a feature extractor or model.
    lengths = []
    for row in test_rows:
        feature = np.load(row["path"], mmap_mode="r", allow_pickle=False)
        require(feature.ndim == 2 and feature.shape[0] > 0, "Invalid feature shape")
        lengths.append(int(feature.shape[0]) * 16)
        del feature
    bounds = np.r_[0, np.cumsum(lengths)]
    scores, truths, metrics, checks = [], [], [], []
    for arm, condition in (("baseline", "B0"), ("ours", cfg["condition"])):
        directory = cfg[arm]
        npz = directory / "frame_scores_and_gt.npz"
        meta = directory / "metrics.json"
        inputs.update((npz, meta))
        with np.load(npz, allow_pickle=False) as stored:
            score = stored[cfg["score_key"]]
            gt = stored[cfg["gt_key"]]
        require(score.ndim == gt.ndim == 1, "Scores and GT must be one-dimensional")
        require(len(score) == len(gt) == bounds[-1], "Frame count mismatch")
        require(np.isfinite(score).all() and np.isfinite(gt).all(), "Nonfinite values")
        require(np.isin(gt, [0, 1]).all(), "GT is not binary")
        require(score.min() >= 0 and score.max() <= 1, "Score outside [0,1]")
        m = read_json(meta)
        if cfg["dataset"] == "UCF":
            alignment_file = directory / "per_video_alignment.csv"
            alignment = read_csv(alignment_file)
            require(len(alignment) == len(test_rows), "Alignment row count differs")
            for i, (a, row, length) in enumerate(zip(alignment, test_rows, lengths)):
                require(int(a["index"]) == i and a["base_video_id"] == names[i],
                        f"UCF video order mismatch at {i}")
                require(a["label"] == row["label"] and int(a["frames"]) == length
                        and int(a["snippets"]) * 16 == length,
                        f"UCF alignment mismatch at {i}")
                require(Path(a["path"]).resolve() == Path(row["path"]).resolve(),
                        f"UCF feature source mismatch at {i}")
        else:
            alignment_file = directory / "alignment.json"
            alignment = read_json(alignment_file)
            require(alignment["videos"] == len(test_rows), "XD alignment count mismatch")
            require([v * 16 for v in alignment["lengths"]] == lengths,
                    "XD feature lengths do not match recorded evaluator order")
        inputs.add(alignment_file)
        # Recover exactly the dataset-specific paper readout, never a nicer branch.
        for metric, actual in ((cfg["ap_metric"], average_precision_score(gt, score)),
                               (cfg["auc_metric"], roc_auc_score(gt, score))):
            matches = [r for r in ledger if r["dataset"] == cfg["dataset"]
                       and r["protocol"] == "clean" and r["condition"] == condition
                       and r["seed"] == str(SEED) and r["metric"] == metric]
            require(len(matches) == 1, f"Missing or ambiguous ledger row: {condition}/{metric}")
            expected = float(matches[0]["value"])
            require(math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10),
                    f"Ledger mismatch: {cfg['dataset']}/{arm}/{metric}: {actual} vs {expected}")
            require(math.isclose(actual, m[metric], rel_tol=0, abs_tol=1e-10),
                    f"Stored metrics mismatch for {arm}/{metric}")
            checks.append(dict(arm=arm, metric=metric, recomputed=float(actual),
                               ledger=expected, absolute_error=abs(float(actual)-expected)))
        scores.append(score)
        truths.append(gt)
        metrics.append(m)
    require(np.array_equal(*truths), "Baseline and Ours GT differ")
    gt, baseline, ours = truths[0], scores[0], scores[1]
    rows = []
    for i, row in enumerate(test_rows):
        start, end = map(int, bounds[i:i + 2])
        g, b, o = gt[start:end], baseline[start:end], ours[start:end]
        n_abnormal = int(g.sum())
        eligible = 0 < n_abnormal < len(g)
        ap_b = float(average_precision_score(g, b)) if eligible else ""
        ap_o = float(average_precision_score(g, o)) if eligible else ""
        rows.append(dict(dataset=cfg["dataset"], seed=SEED, protocol="clean",
                         test_index=i, video=names[i], label=row["label"],
                         score_key=cfg["score_key"], frame_start_concat=start,
                         frame_end_concat_exclusive=end, n_frames=len(g),
                         n_normal=len(g)-n_abnormal, n_abnormal=n_abnormal,
                         eligible=eligible,
                         exclusion_reason="" if eligible else "GT_has_only_one_class",
                         ap_vadclip=ap_b, ap_ours=ap_o,
                         delta_ap=ap_o-ap_b if eligible else "",
                         delta_ap_pp=100*(ap_o-ap_b) if eligible else "",
                         rank_all_candidates="", rank_fraction="", in_middle_50pct=False,
                         selected=False, selection_reason="", feature_path=row["path"]))
    pick, summary = select(rows)
    start, end = pick["frame_start_concat"], pick["frame_end_concat_exclusive"]
    g, b, o = gt[start:end], baseline[start:end], ours[start:end]
    diagnostics = dict(gt_abnormal_intervals=segments(g),
                       normal_mean_vadclip=float(b[g == 0].mean()),
                       normal_mean_ours=float(o[g == 0].mean()),
                       abnormal_mean_vadclip=float(b[g == 1].mean()),
                       abnormal_mean_ours=float(o[g == 1].mean()),
                       mean_absolute_score_difference=float(np.abs(o-b).mean()),
                       abnormal_fraction_ours_higher=float((o[g == 1] > b[g == 1]).mean()),
                       normal_fraction_ours_lower=float((o[g == 0] < b[g == 0]).mean()))
    return dict(config=cfg, rows=rows, pick=pick, summary=summary,
                diagnostics=diagnostics, gt=g, baseline=b, ours=o,
                metrics=metrics, ledger_checks=checks)


def step_vertices(values):
    """Lossless constant-run compression; no smoothing or downsampling."""
    starts = np.r_[0, np.flatnonzero(np.diff(values) != 0) + 1]
    return np.r_[starts, len(values)], np.r_[values[starts], values[-1]]


def plot(datasets, directory):
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                         "font.size": 7.5, "axes.labelsize": 8, "axes.titlesize": 8,
                         "xtick.labelsize": 7, "ytick.labelsize": 7,
                         "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
                         "axes.linewidth": 0.6, "axes.spines.top": False,
                         "axes.spines.right": False, "path.simplify": False})
    fig, axes = plt.subplots(2, 1, figsize=(3.5, 3.35))
    fig.subplots_adjust(left=0.15, right=0.985, bottom=0.115, top=0.855, hspace=0.66)
    blue, orange, grey = "#0072B2", "#D55E00", "0.88"
    for letter, ax, ds in zip("ab", axes, datasets):
        n = len(ds["gt"])
        for start, end in segments(ds["gt"]):
            ax.axvspan(start, end, color=grey, linewidth=0, zorder=0)
        ax.step(*step_vertices(ds["ours"]), where="post", color=orange, lw=0.9, zorder=2)
        ax.step(*step_vertices(ds["baseline"]), where="post", color=blue,
                lw=0.85, linestyle=(0, (3, 1.8)), zorder=3)
        ax.set(xlim=(0, n), ylim=(-0.025, 1.025), xlabel="Frame", ylabel="Anomaly score",
               title=f"({letter}) {ds['config']['title']} example")
        ax.set_yticks([0, 0.5, 1], ["0", "0.5", "1"])
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
        ax.tick_params(width=0.6, length=2.5, pad=2)
        ax.set_title(ax.get_title(), loc="center", pad=4)
    fig.legend(handles=[Line2D([], [], color=blue, lw=0.9, linestyle=(0, (3, 1.8)), label="VadCLIP"),
                        Line2D([], [], color=orange, lw=0.9, label="Ours"),
                        Patch(facecolor=grey, edgecolor="none", label="Ground truth")],
               loc="upper center", bbox_to_anchor=(0.55, 0.998), ncol=3, frameon=False,
               fontsize=7.2, handlelength=1.8, columnspacing=1.1)
    # Fixed canvas preserves the exact intended single-column print dimensions.
    metadata = {"Title": "Frame-level anomaly localization: fixed median-near selection",
                "Creator": "make_qualitative_representative.py",
                "CreationDate": None, "ModDate": None}
    fig.savefig(directory / f"{STEM}.pdf", metadata=metadata)
    fig.savefig(directory / f"{STEM}.png", dpi=600)
    plt.close(fig)


def report(datasets, manifest):
    lines = ["# Representative qualitative selection", "",
             "## Scope and figure contract", "",
             "This figure compares existing raw scores on two real test videos; it does not establish "
             "uniformly stronger abnormal responses or reduced normal activation. Quantitative-grid archetype: "
             "two equal time-series panels, one per dataset. Python/matplotlib only; 2 rows x 1 column, "
             "3.5 x 3.35 inches (88.9 x 85.09 mm), embedded TrueType PDF and 600 dpi PNG. "
             "Labels 8 pt; ticks 7 pt; legend 7.2 pt. One matched seed, two illustrative videos; "
             "no confidence intervals or significance claims apply to these individual traces.", "",
             "No training, checkpoint loading, inference, source prediction editing, or main-result changes. "
             "Feature files are opened only to read their existing array shapes.", "",
             "## Fixed rule (declared before inspecting per-video results)", "",
             f"Rule ID: `{RULE}`.", "",
             "1. Freeze the clean/fixed-epoch matched experiment and seed 234 (smallest seed), "
             "without searching seeds, checkpoints, protocols, branches, categories, or visual appearance.",
             "2. Use the paper's dataset-specific readout: UCF `frame_scores_prob1` (classification, "
             "headline AUC1); XD `scores` (semantic, headline AP2). AP is the selection statistic "
             "for both datasets; UCF per-video AP is not its headline benchmark metric.",
             "3. Check all test videos in list order, both arms' lengths, finite [0,1] scores, binary GT, "
             "identical GT, feature-header lengths, and saved alignment. Any malformed input aborts "
             "the run rather than silently shrinking the candidate pool. A candidate has both GT classes. "
             "No extra label, duration, effect-size, or appearance filter is used.",
             "4. Compute sklearn average_precision_score on every candidate's complete frame sequence. "
             "Set delta_AP = AP(Ours) - AP(VadCLIP), sort ALL candidates by (delta_AP ascending, "
             "test-list index ascending), and use one-based ranks r. The target median rank is (N+1)/2.",
             "5. Define middle 50% objectively by 0.25 <= (r-1)/(N-1) <= 0.75 "
             "(0.5 for N=1). Among positive candidates in this band, minimize "
             "(distance to median rank, delta_AP, test-list index). Positive means delta_AP > 1e-12. "
             "The tolerance only suppresses floating-point zero.",
             "6. If the band contains no positive candidate, choose the smallest positive delta_AP "
             "in the complete pool, breaking ties by test-list index. If there is no positive candidate "
             "anywhere, stop and report that the requirement cannot be met.",
             "7. Do not replace the deterministic selections after viewing their curves. Keep the "
             "whole video, [0,1] score scale, and exact GT intervals. No temporal crop, smoothing, "
             "interpolation, per-video normalization, or score transformation. Step plotting compresses "
             "only exactly identical adjacent values, preserving every raw score and boundary.", "",
             "The median is over ALL eligible videos, not over positives alone. This is still "
             "outcome-conditioned selection: these are median-near positive examples, not an unbiased "
             "sample or evidence of whole-test-set generalization. The rule is reproducible but was "
             "specified after the underlying experiments; it is not a preregistered experimental protocol.", "",
             "## Selections", "",
             "| Dataset | Video / feature ID | Test index (0-based) | Rank / candidates | AP VadCLIP | AP Ours | Delta AP (pp) |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for ds in datasets:
        r, s = ds["pick"], ds["summary"]
        lines.append(f"| {ds['config']['title']} | `{r['video']}` | {r['test_index']} | "
                     f"{r['rank_all_candidates']} / {s['n_candidates']} | {100*r['ap_vadclip']:.8f} | "
                     f"{100*r['ap_ours']:.8f} | {r['delta_ap_pp']:+.8f} |")
    for ds in datasets:
        r, s, d = ds["pick"], ds["summary"], ds["diagnostics"]
        lines += ["", f"### {ds['config']['title']}", "",
                  f"Test videos: {s['n_test']}; mixed-GT candidates: {s['n_candidates']}; "
                  f"positive / negative / zero: {s['n_positive']} / {s['n_negative']} / {s['n_zero']}. "
                  f"All-candidate mean delta: {s['mean_delta_ap']*100:+.8f} pp; "
                  f"median: {s['median_delta_ap']*100:+.8f} pp. Selection: `{r['selection_reason']}`.", "",
                  f"Frames: {r['n_frames']} ({r['n_normal']} normal, {r['n_abnormal']} abnormal). "
                  f"Abnormal intervals, zero-based [start,end): `{d['gt_abnormal_intervals']}`.", "",
                  f"Normal-region mean score, VadCLIP -> Ours: {d['normal_mean_vadclip']:.6f} -> "
                  f"{d['normal_mean_ours']:.6f}; abnormal-region mean: "
                  f"{d['abnormal_mean_vadclip']:.6f} -> {d['abnormal_mean_ours']:.6f}. "
                  "These are diagnostics, not additional selection criteria."]
    lines += ["", "## Source and alignment audit", "",
              "Both arms' global AP and AUC were recomputed from the saved predictions and checked "
              "against the clean-protocol results ledger and original metrics.json (absolute tolerance "
              "1e-10). Every check is recorded in the manifest. Checkpoints are identified by their "
              "existing metadata hashes; model files are never opened.", "",
              "XD uses the ORIGINAL stage-2 baseline archive, which matches the ledger, instead of "
              "the later re-evaluation copy used by the old figure. The old description of XD `scores` "
              "as binary-branch AP2 was incorrect: the evaluator saves 1 - softmax(logits2)[normal]. "
              "UCF uses sigmoid(logits1). Both evaluators repeat each snippet score over 16 frames. "
              "The horizontal axis is the saved evaluation-frame index; FPS is not inferred.", "",
              "UCF names/order/paths/labels and snippet/frame lengths are checked against each arm's "
              "per_video_alignment.csv. XD has no saved per-frame IDs: its order is reconstructed "
              "from the existing test list and verified against both alignment.json length vectors "
              "and all 800 feature headers, following the archived evaluator. This documents the "
              "available alignment evidence rather than claiming independent decoded-video validation.", "",
              "| Dataset | Arm | Saved predictions | Recorded checkpoint SHA256 |",
              "|---|---|---|---|"]
    for ds in datasets:
        for arm, m in zip(("baseline", "ours"), ds["metrics"]):
            lines.append(f"| {ds['config']['title']} | {arm} | "
                         f"`{ds['config'][arm] / 'frame_scores_and_gt.npz'}` | "
                         f"`{m['checkpoint_sha256']}` |")
    lines += ["", "## Reproduce", "", "```powershell",
              f"Set-Location '{ROOT}'", "python scripts/make_qualitative_representative.py",
              "```", "",
              "Existing outputs are protected: use `--overwrite` only when intentionally replacing "
              "this figure package, or use `--output-root <new-directory>` for independent reproduction. "
              "The script reads source artifacts relative to its repository, not the current directory.", "",
              "Outputs: selection.csv contains the two picks; candidates.csv lists every test video, "
              "including exclusions and all eligible AP values/ranks; summary.csv gives the complete "
              "candidate distributions; source_data.csv contains every plotted frame. "
              "The manifest records input/output SHA256 hashes, package versions, git HEAD, "
              "score keys, source paths, and metric checks.", "",
              f"Python {manifest['versions']['python']}; numpy {np.__version__}; "
              f"scikit-learn {sklearn.__version__}; matplotlib {matplotlib.__version__}.", "",
              "## Conservative caption", "", CAPTION, "",
              "Main-text suitability and the optional LaTeX insertion are reviewed separately in "
              "`qualitative_representative_review.md`. This selection report does not modify main.tex "
              "or establish a six-page layout pass.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    evidence = args.output_root.resolve() / "evidence"
    figures = args.output_root.resolve() / "paper/figures"
    outputs = [evidence / f"{STEM}_{name}.{ext}" for name, ext in
               (("selection", "csv"), ("selection", "md"), ("candidates", "csv"),
                ("summary", "csv"), ("source_data", "csv"), ("manifest", "json"))]
    outputs += [figures / f"{STEM}.{ext}" for ext in ("pdf", "png")]
    if not args.overwrite:
        require(not any(p.exists() for p in outputs),
                "An output already exists; use a new --output-root or explicitly --overwrite")
    ledger_path = ROOT / "evidence/results_ledger.csv"
    inputs = {ledger_path, Path(__file__).resolve(),
              S2 / "code/evaluate_checkpoint_with_scores.py", S11 / "src/evaluate_xd.py"}
    ledger = read_csv(ledger_path)
    datasets = [load_dataset(cfg, ledger, inputs) for cfg in CONFIGS]
    manifest = dict(rule_id=RULE, seed=SEED, protocol="clean", positive_tolerance=EPS,
                    git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    versions=dict(python=platform.python_version(), numpy=np.__version__,
                                  sklearn=sklearn.__version__, matplotlib=matplotlib.__version__),
                    inputs=[dict(path=str(p.resolve()), sha256=sha256(p)) for p in sorted(inputs)],
                    datasets=[dict(dataset=d["config"]["dataset"], score_key=d["config"]["score_key"],
                                   selection=d["pick"], summary=d["summary"], diagnostics=d["diagnostics"],
                                   ledger_checks=d["ledger_checks"]) for d in datasets])
    evidence.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    write_csv(outputs[0], [d["pick"] for d in datasets])
    outputs[1].write_text(report(datasets, manifest), encoding="utf-8")
    write_csv(outputs[2], [r for d in datasets for r in d["rows"]])
    write_csv(outputs[3], [dict(dataset=d["config"]["dataset"], **d["summary"]) for d in datasets])
    source_rows = [dict(dataset=d["config"]["dataset"], video=d["pick"]["video"], frame=i,
                        vadclip=float(b), ours=float(o), ground_truth=int(g))
                   for d in datasets for i, (b, o, g) in enumerate(zip(d["baseline"], d["ours"], d["gt"]))]
    write_csv(outputs[4], source_rows)
    plot(datasets, figures)
    # Verify all read-only source inputs remain unchanged during execution.
    require(all(sha256(item["path"]) == item["sha256"] for item in manifest["inputs"]),
            "A source input changed during the run")
    manifest["outputs"] = [dict(path=str(p), sha256=sha256(p)) for p in outputs if p != outputs[5]]
    outputs[5].write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for d in datasets:
        r = d["pick"]
        print(f"{r['dataset']}: {r['video']} | rank {r['rank_all_candidates']}/{d['summary']['n_candidates']} "
              f"| delta AP {r['delta_ap_pp']:+.8f} pp")
    print(f"Saved {figures / STEM}.pdf and .png; source inputs unchanged.")


if __name__ == "__main__":
    main()
