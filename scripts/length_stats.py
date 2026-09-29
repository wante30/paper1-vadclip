"""Snippet-length statistics per split (read-only; uses mmap to read .npy headers).

Answers: for what fraction of videos does VadCLIP's train-time aggregation
(uniform segment-mean pooling to 256) actually average, versus pad only?
At test time process_split never averages; it cuts non-overlapping windows.
"""
import csv
import sys

import numpy as np
import pandas as pd

LISTS = {
    "UCF_train": r"C:\Projects\baseline-first\vadclip_protocol_audit\assets\lists_local\ucf_train.csv",
    "UCF_test": r"C:\Projects\baseline-first\vadclip_protocol_audit\assets\lists_local\ucf_test.csv",
    "XD_train": r"C:\Projects\baseline-first\vadclip_method_stage2\assets\xd_vadclip_official\list\xd_CLIP_rgb_local.csv",
    "XD_test": r"C:\Projects\baseline-first\vadclip_method_stage2\assets\xd_vadclip_official\list\xd_CLIP_rgbtest_local.csv",
}
T = 256
out_rows = []
for name, path in LISTS.items():
    df = pd.read_csv(path)
    lengths = np.array([np.load(p, mmap_mode="r").shape[0] for p in df["path"]])
    over = lengths > T
    row = {
        "split": name, "items": len(lengths), "min": int(lengths.min()), "median": float(np.median(lengths)),
        "max": int(lengths.max()), "frac_len_gt_256": float(over.mean()),
        "mean_bin_size_when_averaged": float((lengths[over] / T).mean()) if over.any() else 0.0,
    }
    out_rows.append(row)
    print(row, flush=True)

with open(sys.argv[1], "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
    w.writeheader()
    w.writerows(out_rows)
