"""Loose arXiv lookup for candidates that missed exact-title matching.

Prints the top hits for a short keyword query so each match can be checked by
hand. Also queries Semantic Scholar (by arXiv id) for venue of already-identified
papers whose arXiv comment gives no venue. Read-only; writes refs/candidates_loose.csv.
"""
from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
UA = {"User-Agent": "paper1-citation-check/0.1"}

LOOSE = [
    ("rtfm", "robust temporal feature magnitude"),
    ("msl", "multi-sequence learning transformer anomaly"),
    ("s3r", "self-supervised sparse representation anomaly"),
    ("urdmu", "dual memory units uncertainty regulation"),
    ("tpwng", "text prompt normality guidance"),
    ("stprompt", "spatio-temporal prompts anomaly"),
    ("gcn", "semi-supervised classification graph convolutional networks"),
    ("clipadapter", "CLIP-Adapter feature adapters"),
]
VENUE_BY_ARXIV = [("mgfn", "2211.15098"), ("pel4vad", "2306.14451"), ("holmesvad", "2406.12235"),
                  ("adapter", "1902.00751"), ("lora", "2106.09685")]


def arxiv_hits(words: str, n: int = 4):
    q = " AND ".join(f'ti:"{w}"' if "-" in w else f"ti:{w}" for w in words.split())
    url = "http://export.arxiv.org/api/query?max_results=%d&search_query=%s" % (n, urllib.parse.quote(q))
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        root = ET.fromstring(r.read())
    out = []
    for e in root.findall("a:entry", NS):
        out.append({
            "title": " ".join(e.findtext("a:title", "", NS).split()),
            "arxiv_id": e.findtext("a:id", "", NS).rsplit("/", 1)[-1],
            "authors": "; ".join(a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)[:3]),
            "comment": " ".join(e.findtext("x:comment", "", NS).split()),
        })
    return out


def s2_venue(arxiv_id: str):
    url = ("https://api.semanticscholar.org/graph/v1/paper/arXiv:%s?fields=title,venue,year,"
           "publicationVenue,externalIds" % arxiv_id)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return json.loads(r.read())


def main():
    rows = []
    for key, words in LOOSE:
        try:
            hits = arxiv_hits(words)
        except Exception as exc:
            hits = [{"title": f"ERROR {exc}"}]
        print(f"=== {key}: {words}")
        for h in hits or [{"title": "NO HIT"}]:
            print(f"   {h.get('arxiv_id', '-'):14} {h['title'][:95]} | {h.get('comment', '')[:60]}")
            rows.append({"key": key, "source": "arxiv_loose", **h})
        time.sleep(4)
    for key, aid in VENUE_BY_ARXIV:
        try:
            p = s2_venue(aid)
            rec = {"title": p.get("title", ""), "arxiv_id": aid,
                   "comment": f"venue={p.get('venue')} year={p.get('year')} dblp={p.get('externalIds', {}).get('DBLP')}"}
        except Exception as exc:
            rec = {"title": f"ERROR {exc}", "arxiv_id": aid}
        print(f"=== venue {key}: {rec['title'][:70]} | {rec.get('comment', '')}")
        rows.append({"key": key, "source": "s2_venue", **rec})
        time.sleep(6)
    with (ROOT / "refs" / "candidates_loose.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["key", "source", "title", "arxiv_id", "authors", "comment"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
