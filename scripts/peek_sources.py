"""Read-only peek at nested fields of source ledgers used by build_ledger.py."""
import json

EXP = r"C:\Projects\baseline-first\vadclip_method_stage11_isolated_semantic_posttrain"


def load(path):
    with open(path, encoding="utf-8-sig") as handle:
        return json.load(handle)


def peek(label, value, n=500):
    print(f"== {label}: {json.dumps(value)[:n]}")


a = load(EXP + r"\XD_OFFICIAL_CHECKPOINT_ADAPTATION.json")
peek("adaptation.branches[0]", a["branches"][0] if a["branches"] else None)
peek("adaptation.branches len", len(a["branches"]), 20)
peek("adaptation.pairs", a["pairs"])
peek("adaptation.summary", a["summary"])

f = load(r"C:\Projects\baseline-first\FINAL_EVIDENCE_LEDGER_20260926.json")
for name in ("table_A_ucf_final_matched_seeds", "table_B_xd_final_matched_seeds", "table_D_g_cross_dataset_conflict"):
    table = f[name]
    sample = table[0] if isinstance(table, list) else table
    peek(f"{name} ({type(table).__name__}, n={len(table)})", sample)

r = load(EXP + r"\STAGE13_XD_RELEASED_PROTOCOL.json")
b0 = r["runs"]["234"]["B0"]
peek("stage13.234.B0.selected_epoch", b0["selected_epoch"], 50)
peek("stage13.234.B0.selected_metrics", b0["selected_metrics"], 250)
peek("stage13.234.B0.final_epoch_metrics", b0["final_epoch_metrics"], 250)
peek("stage13.234.B0.config", b0["config"], 400)

u = load(r"C:\Projects\baseline-first\vadclip_protocol_audit\results\seed234\E0_released_checkpoint\metrics.json")
peek("ucf official released ckpt", u)
