"""Build the paper evidence ledger from experiment artifacts (read-only on sources).

Outputs (evidence/): results_ledger.csv, aggregates.csv, paired_deltas.csv,
coverage.csv, consistency_checks.csv, sources_manifest.csv.
Every number used in the paper must trace to a row here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

BF = Path(r"C:\Projects\baseline-first")
EXP = BF / "vadclip_method_stage11_isolated_semantic_posttrain"
OUT = Path(__file__).resolve().parent.parent / "evidence"
METRICS = ("AUC1", "AP1", "AUC2", "AP2")
rows: list[dict] = []
sources: dict[str, str] = {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(path: Path):
    sources.setdefault(str(path), sha256(path))
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def dig(obj, keypath: str):
    for k in keypath.split(".") if keypath else []:
        obj = obj[int(k)] if isinstance(obj, list) else obj[k]
    return obj


def add(dataset, protocol, condition, seed, path: Path, keypath: str = "", note: str = ""):
    """Record AUC1/AP1/AUC2/AP2/dMAP_avg for one run from one source file."""
    m = dig(load(path), keypath)
    values = {k: m.get(k) for k in METRICS}
    d = m.get("dMAP")
    values["dMAP_avg"] = (sum(d) / len(d)) if isinstance(d, list) else d
    for metric, value in values.items():
        if value is None:
            continue
        rows.append({"dataset": dataset, "protocol": protocol, "condition": condition, "seed": seed,
                     "metric": metric, "value": repr(float(value)), "source": str(path),
                     "keypath": keypath, "note": note})


FINAL_LEDGER = BF / "FINAL_EVIDENCE_LEDGER_20260926.json"
SEEDS = ("234", "235", "236")


def collect_ucf():
    for s in SEEDS:
        # B0 / A / AE clean matched seeds (ledger table A; A missing where never run)
        for cond, key in (("B0", "B0"), ("A", "A"), ("AE", "A_plus_E")):
            table = load(FINAL_LEDGER)["table_A_ucf_final_matched_seeds"]
            if s in table and isinstance(table[s].get(key), dict) and table[s][key].get("AUC1") is not None:
                add("UCF", "clean", cond, s, FINAL_LEDGER, f"table_A_ucf_final_matched_seeds.{s}.{key}")
    # Final = AE + protected T (per-run evaluator outputs)
    add("UCF", "clean", "Final", "234", EXP / "results/ucf_seed234/T_isolated_g_post/official_eval/metrics.json")
    for s in ("235", "236"):
        add("UCF", "clean", "Final", s, EXP / f"results/ucf_seed{s}/final_protected_g/official_eval/metrics.json")
    # POST-aggregation control (placement)
    for s in ("234", "235"):
        add("UCF", "clean", "POST", s, EXP / "UCF_PRE_VS_POST_VARIATION.json", f"results.{s}.POST_AE")
    add("UCF", "clean", "POST", "236", EXP / "results/ucf_seed236/POST_variation_eval/metrics.json")
    # E standalone, full-network G (seed234 only)
    add("UCF", "clean", "E_only", "234", EXP / "STAGE12D_FACTORIAL_ABLATION.json", "results.UCF234.E")
    add("UCF", "clean", "fullG", "234", FINAL_LEDGER, "table_D_g_cross_dataset_conflict.UCF_seed234.A_plus_E_plus_G")
    # Official released checkpoint re-evaluated with our evaluator
    add("UCF", "official", "R", "ref", BF / "vadclip_protocol_audit/results/seed234/E0_released_checkpoint/metrics.json")


def collect_xd():
    xdg = EXP / "XD_PROTECTED_G_3SEED_COMPARISON.json"
    for s in SEEDS:
        for cond in ("B0", "AE", "C", "T"):
            add("XD", "clean", cond, s, xdg, f"seeds.{s}.{cond}")
        table = load(FINAL_LEDGER)["table_B_xd_final_matched_seeds"]
        if isinstance(table.get(s, {}).get("A"), dict) and table[s]["A"].get("AP2") is not None:
            add("XD", "clean", "A", s, FINAL_LEDGER, f"table_B_xd_final_matched_seeds.{s}.A")
    for s in ("234", "235"):
        add("XD", "clean", "B0T", s, EXP / "XD_B0_PROTECTED_ATTRIBUTION.json", f"seeds.{s}.B0T")
    add("XD", "clean", "B0T", "236", EXP / "results/xd_seed236/B0_protected_g/official_eval/metrics.json")
    add("XD", "clean", "E_only", "234", EXP / "STAGE12D_FACTORIAL_ABLATION.json", "results.XD234.E")
    add("XD", "clean", "fullG", "234", FINAL_LEDGER, "table_D_g_cross_dataset_conflict.XD_seed234.A_plus_E_plus_G")
    add("XD", "official", "R", "ref", EXP / "XD_OFFICIAL_CHECKPOINT_ADAPTATION.json", "official_R")
    adapt = load(EXP / "XD_OFFICIAL_CHECKPOINT_ADAPTATION.json")["branches"]
    for i, b in enumerate(adapt):
        add("XD", "official_adapt", "R" + b["arm"], str(b["seed"]), EXP / "XD_OFFICIAL_CHECKPOINT_ADAPTATION.json", f"branches.{i}.metrics")
    rel = EXP / "STAGE13_XD_RELEASED_PROTOCOL.json"
    for s in SEEDS:
        for cond in ("B0", "AE", "C", "T"):
            add("XD", "released_selected", cond, s, rel, f"runs.{s}.{cond}.selected_metrics")
            add("XD", "released_final", cond, s, rel, f"runs.{s}.{cond}.final_epoch_metrics")


MANUAL = OUT / "manual" / "xd_official_protocol_remote4090.csv"


def collect_manual():
    """Hand-entered results (remote 4090 official-protocol rerun) until metrics.json files are pulled in."""
    sources.setdefault(str(MANUAL), sha256(MANUAL))
    with MANUAL.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"dataset": r["dataset"], "protocol": r["protocol"], "condition": r["condition"],
                         "seed": r["seed"], "metric": r["metric"], "value": repr(float(r["value_pct"]) / 100),
                         "source": str(MANUAL), "keypath": "", "note": "manual: " + r["note"]})


# (dataset, metric, (protocol_a, cond_a), (protocol_b, cond_b)) -> delta = a - b, in pp
DELTAS = [
    ("UCF", "AUC1", ("clean", "AE"), ("clean", "B0")),
    ("UCF", "AUC1", ("clean", "Final"), ("clean", "B0")),
    ("UCF", "AUC1", ("clean", "Final"), ("clean", "AE")),
    ("UCF", "AUC1", ("clean", "A"), ("clean", "B0")),
    ("UCF", "AUC1", ("clean", "AE"), ("clean", "A")),
    ("UCF", "AUC1", ("clean", "AE"), ("clean", "POST")),
    ("UCF", "AUC1", ("clean", "POST"), ("clean", "B0")),
    ("UCF", "AUC1", ("clean", "E_only"), ("clean", "B0")),
    ("UCF", "AUC1", ("clean", "fullG"), ("clean", "AE")),
    ("UCF", "AP2", ("clean", "Final"), ("clean", "AE")),
    ("UCF", "AUC1", ("clean", "B0"), ("official", "R")),
    ("XD", "AP2", ("clean", "T"), ("clean", "B0")),
    ("XD", "AP2", ("clean", "T"), ("clean", "AE")),
    ("XD", "AP2", ("clean", "T"), ("clean", "C")),
    ("XD", "AP2", ("clean", "AE"), ("clean", "B0")),
    ("XD", "AP2", ("clean", "A"), ("clean", "B0")),
    ("XD", "AP2", ("clean", "B0T"), ("clean", "B0")),
    ("XD", "AP2", ("clean", "T"), ("clean", "B0T")),
    ("XD", "AP2", ("clean", "E_only"), ("clean", "B0")),
    ("XD", "AP2", ("clean", "fullG"), ("clean", "AE")),
    ("XD", "AP1", ("clean", "T"), ("clean", "B0")),
    ("XD", "AP2", ("clean", "B0"), ("official", "R")),
    ("XD", "AP2", ("released_selected", "AE"), ("released_selected", "B0")),
    ("XD", "AP2", ("released_selected", "T"), ("released_selected", "B0")),
    ("XD", "AP2", ("released_selected", "T"), ("released_selected", "C")),
    ("XD", "AP2", ("released_final", "T"), ("released_final", "B0")),
    ("XD", "AP2", ("released_selected", "B0"), ("released_final", "B0")),
    ("XD", "AP2", ("released_selected", "B0"), ("clean", "B0")),
    ("XD", "AP2", ("official_adapt", "RC"), ("official", "R")),
    ("XD", "AP2", ("official_adapt", "RT"), ("official", "R")),
    ("XD", "AP2", ("official_adapt", "RT"), ("official_adapt", "RC")),
    ("XD", "AP2", ("official_rerun", "T"), ("official_rerun", "B0")),
]


def lookup():
    table = {}
    for r in rows:
        table[(r["dataset"], r["protocol"], r["condition"], r["seed"], r["metric"])] = float(r["value"])
    return table


def seeds_of(table, ds, proto, cond, metric):
    return {k[3]: v for k, v in table.items() if k[:3] == (ds, proto, cond) and k[4] == metric}


def summarize(values):
    n = len(values)
    return {"n": n, "mean": statistics.fmean(values) if n else None,
            "sd": statistics.stdev(values) if n > 1 else None,
            "min": min(values) if n else None, "max": max(values) if n else None}


def compute_deltas(table):
    out = []
    for ds, metric, (pa, ca), (pb, cb) in DELTAS:
        a = seeds_of(table, ds, pa, ca, metric)
        b = seeds_of(table, ds, pb, cb, metric)
        if "ref" in b and "ref" not in a:
            pairs = {s: (a[s] - b["ref"]) * 100 for s in a}
        else:
            pairs = {s: (a[s] - b[s]) * 100 for s in sorted(set(a) & set(b))}
        st = summarize(list(pairs.values()))
        out.append({"dataset": ds, "metric": metric, "a": f"{pa}:{ca}", "b": f"{pb}:{cb}",
                    "seeds": ";".join(pairs), "per_seed_pp": ";".join(repr(v) for v in pairs.values()),
                    "n": st["n"], "n_positive": sum(v > 0 for v in pairs.values()),
                    "mean_pp": st["mean"], "sd_pp": st["sd"]})
    return out


def compute_aggregates(table):
    groups = {}
    for (ds, proto, cond, seed, metric), v in table.items():
        groups.setdefault((ds, proto, cond, metric), {})[seed] = v
    out = []
    for (ds, proto, cond, metric), by_seed in sorted(groups.items()):
        st = summarize(list(by_seed.values()))
        out.append({"dataset": ds, "protocol": proto, "condition": cond, "metric": metric,
                    "seeds": ";".join(sorted(by_seed)), **st})
    return out


def consistency_checks(table, deltas):
    """Cross-check ledger values against independent copies in other artifacts."""
    checks = []

    def check(label, got, expected, tol=1e-9):
        ok = got is not None and expected is not None and abs(got - expected) <= tol
        checks.append({"check": label, "ledger": repr(got), "other_source": repr(expected), "pass": ok})

    xdg = load(EXP / "XD_PROTECTED_G_3SEED_COMPARISON.json")
    tb = load(FINAL_LEDGER)["table_B_xd_final_matched_seeds"]
    for s in SEEDS:
        check(f"XD B0 {s} AP2 protectedG vs ledgerB", table[("XD", "clean", "B0", s, "AP2")], tb[s]["B0"]["AP2"])
        check(f"XD AE {s} AP2 protectedG vs ledgerB", table[("XD", "clean", "AE", s, "AP2")], tb[s]["A_plus_E"]["AP2"])
    att = load(EXP / "XD_B0_PROTECTED_ATTRIBUTION.json")
    for s in ("234", "235"):
        check(f"XD T {s} AP2 protectedG vs attribution AET", table[("XD", "clean", "T", s, "AP2")], att["seeds"][s]["AET"]["AP2"])
    prepost = load(EXP / "UCF_PRE_VS_POST_VARIATION.json")
    ucf3 = load(EXP / "UCF_FINAL_3SEED_COMPARISON.json")
    for s in ("234", "235"):
        check(f"UCF AE {s} AUC1 ledgerA vs prepost PRE_AE", table[("UCF", "clean", "AE", s, "AUC1")], prepost["results"][s]["PRE_AE"]["AUC1"])
        check(f"UCF B0 {s} AUC1 ledgerA vs prepost B0", table[("UCF", "clean", "B0", s, "AUC1")], prepost["results"][s]["B0"]["AUC1"])
    for row in ucf3["primary_table"]:
        s = str(row["seed"])
        check(f"UCF Final {s} AUC1 per-run vs 3seed table", table[("UCF", "clean", "Final", s, "AUC1")], row["Final_AUC1"])
        check(f"UCF AE {s} AUC1 ledgerA vs 3seed table", table[("UCF", "clean", "AE", s, "AUC1")], row["AE_AUC1"])
    comp = load(EXP / "STAGE14_SEED236_COMPLETION.json")
    check("XD B0T 236 AP2 vs stage14 record", table[("XD", "clean", "B0T", "236", "AP2")], comp["R3_xd_seed236_B0_plus_T"]["metrics"]["AP2"])
    check("UCF POST 236 AUC1 vs stage14 record", table[("UCF", "clean", "POST", "236", "AUC1")], comp["R2_ucf_seed236_POST"]["metrics"]["AUC1"])
    check("XD official R AP2 adaptation vs 12R0 eval", table[("XD", "official", "R", "ref", "AP2")],
          load(EXP / "OFFICIAL_XD_CHECKPOINT_EVAL.json")["evaluation"]["AP2"])

    by = {(d["dataset"], d["metric"], d["a"], d["b"]): d for d in deltas}
    agg = xdg["aggregate"]
    check("XD T-B0 AP2 mean pp vs recorded", by[("XD", "AP2", "clean:T", "clean:B0")]["mean_pp"], agg["T_minus_B0_AP2_pp_mean"], 1e-9)
    check("XD T-AE AP2 mean pp vs recorded", by[("XD", "AP2", "clean:T", "clean:AE")]["mean_pp"], agg["T_minus_AE_AP2_pp_mean"], 1e-9)
    check("XD T-C AP2 mean pp vs recorded", by[("XD", "AP2", "clean:T", "clean:C")]["mean_pp"], agg["T_minus_C_AP2_pp_mean"], 1e-9)
    check("UCF Final-B0 AUC1 mean pp vs recorded", by[("UCF", "AUC1", "clean:Final", "clean:B0")]["mean_pp"], ucf3["aggregate"]["Final_minus_B0_pp_mean"], 1e-9)
    check("UCF AE-B0 AUC1 mean pp vs recorded", by[("UCF", "AUC1", "clean:AE", "clean:B0")]["mean_pp"], ucf3["aggregate"]["AE_minus_B0_pp_mean"], 1e-9)
    ad = load(EXP / "XD_OFFICIAL_CHECKPOINT_ADAPTATION.json")["summary"]
    check("XD RC-R AP2 mean pp vs recorded", by[("XD", "AP2", "official_adapt:RC", "official:R")]["mean_pp"], ad["C_minus_R"]["mean_pp"], 1e-9)
    check("XD RT-R AP2 mean pp vs recorded", by[("XD", "AP2", "official_adapt:RT", "official:R")]["mean_pp"], ad["T_minus_R"]["mean_pp"], 1e-9)
    return checks


def write_csv(name, records):
    path = OUT / name
    with path.open("w", encoding="utf-8", newline="") as f:
        if not records:
            f.write("")
            return
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def git_state(repo: Path):
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    return head, (len(dirty.splitlines()) if dirty else 0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    collect_ucf()
    collect_xd()
    collect_manual()
    table = lookup()
    if len(table) != len(rows):
        raise RuntimeError("duplicate (dataset, protocol, condition, seed, metric) keys in ledger")
    deltas = compute_deltas(table)
    aggregates = compute_aggregates(table)
    checks = consistency_checks(table, deltas)
    coverage = [{"dataset": a["dataset"], "protocol": a["protocol"], "condition": a["condition"],
                 "metric": a["metric"], "n": a["n"], "seeds": a["seeds"]} for a in aggregates]
    head, dirty = git_state(EXP)
    manifest = [{"source": p, "sha256": h, "in_experiment_repo": p.startswith(str(EXP)),
                 "experiment_repo_head": head, "experiment_repo_dirty_files": dirty} for p, h in sorted(sources.items())]
    write_csv("results_ledger.csv", rows)
    write_csv("aggregates.csv", aggregates)
    write_csv("paired_deltas.csv", deltas)
    write_csv("coverage.csv", coverage)
    write_csv("consistency_checks.csv", checks)
    write_csv("sources_manifest.csv", manifest)
    failed = [c for c in checks if not c["pass"]]
    print(f"rows={len(rows)} aggregates={len(aggregates)} deltas={len(deltas)} sources={len(sources)}")
    print(f"experiment repo HEAD={head} dirty_files={dirty}")
    print(f"consistency checks: {len(checks) - len(failed)}/{len(checks)} pass")
    for c in failed:
        print("  FAIL", c)
    for d in deltas:
        mean = "NA" if d["mean_pp"] is None else f"{d['mean_pp']:+.4f}"
        sd = "NA" if d["sd_pp"] is None else f"{d['sd_pp']:.4f}"
        print(f"  {d['dataset']:3} {d['metric']:4} {d['a']:>24} - {d['b']:<22} n={d['n']} pos={d['n_positive']} mean={mean} sd={sd}")


if __name__ == "__main__":
    main()
