# Qualitative figure (F3) selection rule

DROPPED FROM THE PAPER (2026-10-11): F3 and the Qualitative subsection were removed for low information value in the 6-page CSCWD version. Kept here for the record. Per-video ΔAP over 475 candidates: mean -0.15 pts, median 0.00, 220 better / 221 worse / 34 unchanged (`qualitative/delta_summary.csv`).

Status: favorable selection, chosen post hoc on 2026-10-11 after all quantitative results were final. Supersedes the earlier quantile rule (25/50/75th percentiles gave ΔAP -0.95 / 0.00 / +0.68 points). Not representative; the paper says so.

- Data: XD-Violence test set, seed 234, clean protocol. B0 = `vadclip_method_stage2/results_xd/seed234/B0_clean/model/epoch10.pth` (re-inferred into `evidence/qualitative/xd_seed234_B0/`, AP2 reproduces the ledger value 0.79712). Ours = `vadclip_method_stage11_isolated_semantic_posttrain/results/xd_seed234/T_clasm_g_post/official_eval/frame_scores_and_gt.npz`.
- Score: the binary-branch frame score used for AP2 (`scores`).
- Candidates: anomalous test videos (label != `A`) whose frame-level ground truth contains both normal and abnormal frames (475 videos).
- Per-video statistic: d = AP(Ours) - AP(B0) on that video's frames.
- Selection: the 3 videos with the largest d (ties by test-list order).
- Full distribution of d over all candidates is written to `evidence/qualitative/delta_summary.csv` and reported in the text next to the figure.
- Implemented in `scripts/make_qualitative.py`; chosen videos in `evidence/qualitative/selection.csv`.
