"""Measure inference latency, peak GPU memory, and parameter counts: B0 vs. Final.

Each configuration runs in its own subprocess because the baseline and PVR model
sources both define a module named `model`. Input is one padded window
(batch 1, T=256, d=512), identical for both arms; the PVR arm also receives a
variation tensor of the same shape. Latency is the median over timed iterations
after warm-up, with CUDA synchronisation around each forward pass.

Usage:  python scripts/measure_complexity.py            (driver, writes evidence/complexity.csv)
        python scripts/measure_complexity.py --worker ...  (internal)
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BF = "C:/Projects/baseline-first"
EXP = BF + "/vadclip_method_stage11_isolated_semantic_posttrain"

# (dataset, arm, mode, source dir, checkpoint, visual_layers, attn_window, classes)
CONFIGS = [
    ("UCF", "B0", "baseline", BF + "/vadclip_protocol_audit/code/src",
     BF + "/vadclip_method_final_seed236/results/ucf_seed236/B0_clean/model/epoch10.pth", 2, 8, 14),
    ("UCF", "Final", "pvr", EXP + "/src/ucf",
     EXP + "/results/ucf_seed236/final_protected_g/model/epoch3.pth", 2, 8, 14),
    ("XD", "B0", "baseline", BF + "/vadclip_protocol_audit/code/src",
     BF + "/vadclip_method_final_xd_seed236/results/xd_seed236/B0_clean/model/epoch10.pth", 1, 64, 7),
    ("XD", "Final", "pvr", EXP + "/src/xd",
     EXP + "/results/xd_seed236/T_clasm_g_post/model/epoch3.pth", 1, 64, 7),
]
UCF_LABELS = ["normal", "abuse", "arrest", "arson", "assault", "burglary", "explosion", "fighting",
              "roadAccidents", "robbery", "shooting", "shoplifting", "stealing", "vandalism"]
XD_LABELS = ["normal", "fighting", "shooting", "riot", "abuse", "car accident", "explosion"]


def worker(a):
    import torch
    sys.path.insert(0, a.src)
    from model import CLIPVAD  # type: ignore

    device = "cuda"
    model = CLIPVAD(a.classes, 512, 256, 512, 1, a.layers, a.attn, 10, 10, device)
    model.load_state_dict(torch.load(a.ckpt, map_location=device))
    model.to(device).eval()
    prompt = UCF_LABELS if a.classes == 14 else XD_LABELS
    g = torch.Generator().manual_seed(0)
    visual = torch.randn(1, 256, 512, generator=g).to(device)
    variation = torch.randn(1, 256, 512, generator=g).abs().to(device)
    lengths = torch.tensor([256], device=device)

    def step():
        if a.mode == "pvr":
            return model(visual, None, prompt, lengths, variation=variation)
        return model(visual, None, prompt, lengths)

    with torch.no_grad():
        for _ in range(a.warmup):
            step()
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(a.iters):
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            step()
            torch.cuda.synchronize()
            times.append((time.perf_counter() - t0) * 1000)
    total = sum(p.numel() for p in model.parameters())
    clip_params = sum(p.numel() for p in model.clipmodel.parameters())
    print(json.dumps({
        "latency_ms_median": statistics.median(times),
        "latency_ms_p10": sorted(times)[len(times) // 10],
        "latency_ms_p90": sorted(times)[(9 * len(times)) // 10],
        "peak_alloc_mb": torch.cuda.max_memory_allocated() / 2**20,
        "params_total": total,
        "params_excl_clip": total - clip_params,
        "gpu": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
    }))


def driver(warmup, iters):
    rows = []
    for ds, arm, mode, src, ckpt, layers, attn, classes in CONFIGS:
        cmd = [sys.executable, __file__, "--worker", "--mode", mode, "--src", src, "--ckpt", ckpt,
               "--layers", str(layers), "--attn", str(attn), "--classes", str(classes),
               "--warmup", str(warmup), "--iters", str(iters)]
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode != 0:
            raise RuntimeError(f"{ds} {arm} failed:\n{out.stderr[-2000:]}")
        r = json.loads(out.stdout.strip().splitlines()[-1])
        rows.append({"dataset": ds, "arm": arm, "checkpoint": ckpt, "warmup": warmup, "iters": iters, **r})
        print(f"{ds:3} {arm:5} median={r['latency_ms_median']:.2f} ms  peak={r['peak_alloc_mb']:.0f} MB  "
              f"params_excl_clip={r['params_excl_clip']:,}", flush=True)
    path = ROOT / "evidence" / "complexity.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--mode"); p.add_argument("--src"); p.add_argument("--ckpt")
    p.add_argument("--layers", type=int); p.add_argument("--attn", type=int); p.add_argument("--classes", type=int)
    p.add_argument("--warmup", type=int, default=20); p.add_argument("--iters", type=int, default=200)
    args = p.parse_args()
    worker(args) if args.worker else driver(args.warmup, args.iters)
