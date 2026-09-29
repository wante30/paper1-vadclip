"""Verify candidate references by exact title on the arXiv API (rate-limited).

Writes refs/candidates_arxiv.csv: query title, matched title, arXiv id, first
authors, published date, and the arXiv comment / journal_ref (venue hints).
A candidate counts as identified only if the matched title equals the query
title after normalisation. Venue still needs the comment/journal_ref or a
second source.
"""
from __future__ import annotations

import csv
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}

CANDIDATES = [
    ("rtfm", "Weakly-supervised Video Anomaly Detection with Robust Temporal Feature Magnitude Learning"),
    ("msl", "Self-Training Multi-Sequence Learning with Transformer for Weakly Supervised Video Anomaly Detection"),
    ("s3r", "Self-Supervised Sparse Representation for Video Anomaly Detection"),
    ("mgfn", "MGFN: Magnitude-Contrastive Glance-and-Focus Network for Weakly-Supervised Video Anomaly Detection"),
    ("urdmu", "Dual Memory Units with Uncertainty Regulation for Weakly Supervised Video Anomaly Detection"),
    ("gcnlnc", "Graph Convolutional Label Noise Cleaner: Train a Plug-and-play Action Classifier for Anomaly Detection"),
    ("cliptsa", "CLIP-TSA: CLIP-Assisted Temporal Self-Attention for Weakly-Supervised Video Anomaly Detection"),
    ("pel4vad", "Learning Prompt-Enhanced Context Features for Weakly-Supervised Video Anomaly Detection"),
    ("tpwng", "Text Prompt with Normality Guidance for Weakly Supervised Video Anomaly Detection"),
    ("stprompt", "Weakly Supervised Video Anomaly Detection and Localization with Spatio-Temporal Prompts"),
    ("lavad", "Harnessing Large Language Models for Training-free Video Anomaly Detection"),
    ("holmesvad", "Holmes-VAD: Towards Unbiased and Explainable Video Anomaly Detection via Multi-modal LLM"),
    ("tdn", "TDN: Temporal Difference Networks for Efficient Action Recognition"),
    ("tsm", "TSM: Temporal Shift Module for Efficient Video Understanding"),
    ("xclip", "Expanding Language-Image Pretrained Models for General Video Recognition"),
    ("gcn", "Semi-Supervised Classification with Graph Convolutional Networks"),
    ("adapter", "Parameter-Efficient Transfer Learning for NLP"),
    ("lora", "LoRA: Low-Rank Adaptation of Large Language Models"),
    ("coop", "Learning to Prompt for Vision-Language Models"),
    ("clipadapter", "CLIP-Adapter: Better Vision-Language Models with Feature Adapters"),
    ("stadapter", "ST-Adapter: Parameter-Efficient Image-to-Video Transfer Learning"),
]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def query(title: str):
    simple = re.sub(r"[^A-Za-z0-9 ]", " ", title)
    q = " AND ".join(f"ti:{w}" for w in simple.split() if len(w) > 3)
    url = "http://export.arxiv.org/api/query?max_results=5&search_query=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "paper1-citation-check/0.1"})
    with urllib.request.urlopen(req, timeout=40) as r:
        root = ET.fromstring(r.read())
    best = None
    for e in root.findall("a:entry", NS):
        t = " ".join(e.findtext("a:title", "", NS).split())
        rec = {
            "matched_title": t,
            "arxiv_id": e.findtext("a:id", "", NS).rsplit("/", 1)[-1],
            "published": e.findtext("a:published", "", NS)[:10],
            "authors": "; ".join(a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)[:3]),
            "comment": " ".join(e.findtext("x:comment", "", NS).split()),
            "journal_ref": " ".join(e.findtext("x:journal_ref", "", NS).split()),
        }
        if norm(t) == norm(title):
            return rec, True
        best = best or rec
    return best, False


def main():
    rows = []
    for key, title in CANDIDATES:
        try:
            rec, exact = query(title)
        except Exception as exc:  # network / rate limit: record and continue
            rec, exact = {"matched_title": f"ERROR {exc}"}, False
        rec = rec or {"matched_title": "NO HIT"}
        rows.append({"key": key, "query_title": title, "exact_title_match": exact, **rec})
        print(f"{key:12} exact={exact!s:5} {rec.get('arxiv_id', '-'):14} | {rec.get('comment', '')[:70]}", flush=True)
        time.sleep(4)
    out = ROOT / "refs" / "candidates_arxiv.csv"
    fields = ["key", "query_title", "exact_title_match", "matched_title", "arxiv_id",
              "published", "authors", "comment", "journal_ref"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("wrote", out, file=sys.stderr)


if __name__ == "__main__":
    main()
