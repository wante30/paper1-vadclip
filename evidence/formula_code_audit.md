# Formula-to-code audit

Source of truth: experiment repo `vadclip_method_stage11_isolated_semantic_posttrain` at commit `cf73778`.
Model source `src/{ucf,xd}/model.py` (sha256 `321a39a0…`, identical role in both datasets). Baseline VadCLIP model `vadclip_protocol_audit/code/src/model.py` (sha256 `6e1cde3d…`), upstream commit `c41067f0`.

## Input aggregation (VadCLIP, unchanged)

| Paper symbol | Code | Location |
|---|---|---|
| X ∈ R^{L×512} raw CLIP snippet features | `np.load(path)` | `src/ucf/utils/variation_dataset.py:64` |
| Train: Agg = uniform segment-mean pooling to T=256 if L>256, else zero-pad | `process_feat` → `uniform_extract(avg=True)` / `pad` | `src/ucf/utils/tools.py:60-90` |
| Test: no averaging; non-overlapping windows of 256, last window zero-padded | `process_split` | `src/ucf/utils/tools.py:92-106` |

Consequence for the paper: "Agg" must be defined as the train-time operator. At test time Agg is a windowing (identity within each window), so V_test = D split into windows. Fraction of training videos that are actually averaged: see `length_stats.csv` (pending).

## Stage 1 — PVR (pre-aggregation variation residual)

| Paper | Code | Location |
|---|---|---|
| D_1 = 0, D_t = \|X_t − X_{t−1}\| on the full raw sequence | `raw_variation` | `variation_dataset.py:19-24`; XD `xd/xd_variation_dataset.py:14-17` |
| A = Agg(X), V = Agg(D) with identical bin boundaries | concatenate [X, D] → `process_feat`/`process_split` → split channels | `variation_dataset.py:32-45` |
| R(V) = W2 GELU(W1 LN(V)), 512→128→512, W2 and b2 zero-init | `variation_residual` | `model.py:126-133` |
| Z = A + β R(V), β = 0.2, injected before position embedding and temporal transformer | `inject_variation_residual` | `model.py:248-255, 264` |
| Params: LN 1,024 + 65,664 + 66,048 = 132,736 | recorded `added_trainable_params` | `STAGE14_SEED236_COMPLETION.json`, `REPORT_STAGE12C_PRE_VS_POST.md` |
| POST control: A = Agg(X), D'_t = \|A_t − A_{t−1}\| | `post_variation` | `variation_dataset_post.py:18-33` |

## Stage 1 — sparse neighbourhood graph refinement (E)

| Paper | Code | Location |
|---|---|---|
| G_orig: cosine similarity, values < 0.7 set to 0, row softmax (zeroed entries keep weight e^0) | `adj4` | `model.py:159-181` |
| G_knn: cosine top-k (k=16, self included), others −inf, row softmax | `sparse_knn_adj` | `model.py:183-196` |
| G = (1−α) G_orig + α G_knn, α = 0.25; used by similarity GCN branch only (gc1, gc2); DistanceAdj unchanged | `refine_similarity_adj`, `encode_video` | `model.py:198-229` |
| Zero added parameters | `new_trainable_parameters: 0` | `STAGE12D_FACTORIAL_ABLATION.json` |

Both PVR and E modify the representation h that feeds both outputs.

## Cascade outputs (VadCLIP, unchanged)

| Paper | Code | Location |
|---|---|---|
| logits1 = f_cls(h + mlp2(h)) | `classifier(visual_features + mlp2(...))` | `model.py:266` |
| a = norm(logits1ᵀ h) (logits1-weighted pooling of h) | `visual_attn` | `model.py:271-274` |
| t_c = t⁰_c + a;  t_c ← t_c + mlp1(t_c) | text path | `model.py:275-278` |
| logits2 = cos(h, t_c) / 0.07 | | `model.py:280-283` |

logits1 does not depend on θ_mlp1 (mlp1 is downstream). logits2 depends on logits1 through a.

## Stage 1 training loss (VadCLIP, unchanged; cite, do not re-derive)

L = L_bin(logits1) + L_CLASM(logits2) + w·L_text. UCF: L_text/13 × 1e-1 (`ucf_train.py:91-93`); XD: L_text/6 × 1e-4 (`xd_train.py:87-89`). Stage-1 method runs use the same weights (`train_ucf_post_variation.py:134-135`, `train_e_only_xd.py:91-92`).

## Stage 2 — pathway-restricted semantic post-training

| Paper | Code | Location |
|---|---|---|
| p_t = 1 − softmax(logits2_t)[normal] | `semantic_anomaly_probability` | `semantic_mil.py:13-16` |
| q = mean of top-k p_t, k = floor(L/16)+1 over valid positions | `semantic_mil_topk_mean` | `semantic_mil.py:19-31` |
| L_G = BCE(q, y), y = 1 for anomalous bag | `semantic_mil_bag_loss` | `semantic_mil.py:34-44` |
| L = L_CLASM + λ L_G, λ = 0.1 | `total = loss_c + 0.1 * loss_g` | `run_stage12b_xd_b0.py:135-137` |
| Only θ_mlp1 trainable (4 tensors, 2,099,712 params); model.eval() with mlp1.train() | requires_grad mask | `run_stage12b_xd_b0.py:109-117, 129` |
| AdamW lr 2e-5, wd 0.01, no scheduler, 3 epochs; batch 96 (XD) / 64 (UCF); fixed seed-derived sample order | | `run_stage12b_xd_b0.py:118, 124, 128`; `UCF_FINAL_CHECKPOINT_LEDGER.json` |
| Isolation check: max\|Δlogits1\| on fixed probe ≤ 1e-7 and zero changed non-mlp1 tensors, else abort | `compare_snapshot` | `run_stage12b_xd_b0.py:64-77, 151-154` |
| Control C: same, λ = 0 (CLASM only) | | `XD_PROTECTED_G_3SEED_COMPARISON.json:protocol` |

## Hyperparameters shared across datasets

β = 0.2, k = 16, α = 0.25 (`src/ucf/model.py:137-140` and `src/xd/model.py:137-140`), λ = 0.1, Stage-2 lr/epochs identical. No per-dataset tuning of method hyperparameters. The Stage-1 training schedule follows released-code defaults per dataset (UCF lr 2e-5, bs 64, milestones [4,8]; XD lr 1e-5, bs 96, milestones [3,6,10]; 10 epochs).
