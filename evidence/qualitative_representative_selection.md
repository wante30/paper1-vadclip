# Representative qualitative selection

## Scope and figure contract

This figure compares existing raw scores on two real test videos; it does not establish uniformly stronger abnormal responses or reduced normal activation. Quantitative-grid archetype: two equal time-series panels, one per dataset. Python/matplotlib only; 2 rows x 1 column, 3.5 x 3.35 inches (88.9 x 85.09 mm), embedded TrueType PDF and 600 dpi PNG. Labels 8 pt; ticks 7 pt; legend 7.2 pt. One matched seed, two illustrative videos; no confidence intervals or significance claims apply to these individual traces.

No training, checkpoint loading, inference, source prediction editing, or main-result changes. Feature files are opened only to read their existing array shapes.

## Fixed rule (declared before inspecting per-video results)

Rule ID: `all-candidate-middle-50pct-nearest-median-positive-v1`.

1. Freeze the clean/fixed-epoch matched experiment and seed 234 (smallest seed), without searching seeds, checkpoints, protocols, branches, categories, or visual appearance.
2. Use the paper's dataset-specific readout: UCF `frame_scores_prob1` (classification, headline AUC1); XD `scores` (semantic, headline AP2). AP is the selection statistic for both datasets; UCF per-video AP is not its headline benchmark metric.
3. Check all test videos in list order, both arms' lengths, finite [0,1] scores, binary GT, identical GT, feature-header lengths, and saved alignment. Any malformed input aborts the run rather than silently shrinking the candidate pool. A candidate has both GT classes. No extra label, duration, effect-size, or appearance filter is used.
4. Compute sklearn average_precision_score on every candidate's complete frame sequence. Set delta_AP = AP(Ours) - AP(VadCLIP), sort ALL candidates by (delta_AP ascending, test-list index ascending), and use one-based ranks r. The target median rank is (N+1)/2.
5. Define middle 50% objectively by 0.25 <= (r-1)/(N-1) <= 0.75 (0.5 for N=1). Among positive candidates in this band, minimize (distance to median rank, delta_AP, test-list index). Positive means delta_AP > 1e-12. The tolerance only suppresses floating-point zero.
6. If the band contains no positive candidate, choose the smallest positive delta_AP in the complete pool, breaking ties by test-list index. If there is no positive candidate anywhere, stop and report that the requirement cannot be met.
7. Do not replace the deterministic selections after viewing their curves. Keep the whole video, [0,1] score scale, and exact GT intervals. No temporal crop, smoothing, interpolation, per-video normalization, or score transformation. Step plotting compresses only exactly identical adjacent values, preserving every raw score and boundary.

The median is over ALL eligible videos, not over positives alone. This is still outcome-conditioned selection: these are median-near positive examples, not an unbiased sample or evidence of whole-test-set generalization. The rule is reproducible but was specified after the underlying experiments; it is not a preregistered experimental protocol.

## Selections

| Dataset | Video / feature ID | Test index (0-based) | Rank / candidates | AP VadCLIP | AP Ours | Delta AP (pp) |
|---|---|---:|---:|---:|---:|---:|
| UCF-Crime | `Stealing062_x264__5` | 133 | 71 / 140 | 59.48272918 | 59.49451487 | +0.01178569 |
| XD-Violence | `v=8oJMGgaww70__#1_label_B4-0-0__0` | 264 | 258 / 475 | 99.97967547 | 99.98051656 | +0.00084109 |

### UCF-Crime

Test videos: 290; mixed-GT candidates: 140; positive / negative / zero: 70 / 64 / 6. All-candidate mean delta: -0.53352595 pp; median: +0.00589284 pp. Selection: `positive_in_middle_50pct_nearest_median_rank`.

Frames: 1552 (862 normal, 690 abnormal). Abnormal intervals, zero-based [start,end): `[(360, 1050)]`.

Normal-region mean score, VadCLIP -> Ours: 0.912911 -> 0.939805; abnormal-region mean: 0.982772 -> 0.985941. These are diagnostics, not additional selection criteria.

### XD-Violence

Test videos: 800; mixed-GT candidates: 475; positive / negative / zero: 218 / 218 / 39. All-candidate mean delta: -0.15234185 pp; median: +0.00000000 pp. Selection: `positive_in_middle_50pct_nearest_median_rank`.

Frames: 3584 (6 normal, 3578 abnormal). Abnormal intervals, zero-based [start,end): `[(0, 3578)]`.

Normal-region mean score, VadCLIP -> Ours: 0.999783 -> 0.999844; abnormal-region mean: 0.999850 -> 0.999903. These are diagnostics, not additional selection criteria.

## Source and alignment audit

Both arms' global AP and AUC were recomputed from the saved predictions and checked against the clean-protocol results ledger and original metrics.json (absolute tolerance 1e-10). Every check is recorded in the manifest. Checkpoints are identified by their existing metadata hashes; model files are never opened.

XD uses the ORIGINAL stage-2 baseline archive, which matches the ledger, instead of the later re-evaluation copy used by the old figure. The old description of XD `scores` as binary-branch AP2 was incorrect: the evaluator saves 1 - softmax(logits2)[normal]. UCF uses sigmoid(logits1). Both evaluators repeat each snippet score over 16 frames. The horizontal axis is the saved evaluation-frame index; FPS is not inferred.

UCF names/order/paths/labels and snippet/frame lengths are checked against each arm's per_video_alignment.csv. XD has no saved per-frame IDs: its order is reconstructed from the existing test list and verified against both alignment.json length vectors and all 800 feature headers, following the archived evaluator. This documents the available alignment evidence rather than claiming independent decoded-video validation.

| Dataset | Arm | Saved predictions | Recorded checkpoint SHA256 |
|---|---|---|---|
| UCF-Crime | baseline | `C:\Projects\baseline-first\vadclip_method_stage2\results\seed234\granularity\B0_E2_clean\frame_scores_and_gt.npz` | `fab0479bc8128d4d4c4a21a173e7b43ba67aa72d1cb35465c2fa7bb1352d81db` |
| UCF-Crime | ours | `C:\Projects\baseline-first\vadclip_method_stage11_isolated_semantic_posttrain\results\ucf_seed234\T_isolated_g_post\official_eval\frame_scores_and_gt.npz` | `039c52b9075fe2ee8bd37af8ab4262f755fdab0a9f98729ba2ea0125d6e33d89` |
| XD-Violence | baseline | `C:\Projects\baseline-first\vadclip_method_stage2\results_xd\seed234\B0_clean\official_eval\frame_scores_and_gt.npz` | `2878bccee2d482fca01523d40ccfff5ea45e35835ecc6374926990bc12950cbf` |
| XD-Violence | ours | `C:\Projects\baseline-first\vadclip_method_stage11_isolated_semantic_posttrain\results\xd_seed234\T_clasm_g_post\official_eval\frame_scores_and_gt.npz` | `736ab382ba214e262c3e151ea97229bbe94c2004ddab6e016deab3a5aa37d6ee` |

## Reproduce

```powershell
Set-Location 'C:\Projects\baseline-first\paper1-vadclip-revision'
python scripts/make_qualitative_representative.py
```

Existing outputs are protected: use `--overwrite` only when intentionally replacing this figure package, or use `--output-root <new-directory>` for independent reproduction. The script reads source artifacts relative to its repository, not the current directory.

Outputs: selection.csv contains the two picks; candidates.csv lists every test video, including exclusions and all eligible AP values/ranks; summary.csv gives the complete candidate distributions; source_data.csv contains every plotted frame. The manifest records input/output SHA256 hashes, package versions, git HEAD, score keys, source paths, and metric checks.

Python 3.13.13; numpy 2.4.6; scikit-learn 1.9.0; matplotlib 3.11.0.

## Conservative caption

Frame-level anomaly scores on UCF-Crime and XD-Violence for fixed, median-near positive-AP examples (matched seed 234). Shading denotes ground-truth abnormal segments. The selected curves remain similar; positive per-video AP differences do not imply reduced normal-region activation.

Main-text suitability and the optional LaTeX insertion are reviewed separately in `qualitative_representative_review.md`. This selection report does not modify main.tex or establish a six-page layout pass.
