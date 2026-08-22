"""Re-verify the real-data ground truth after a fresh download, and patch it in.

The 311 export is live: every `make data` pulls a bigger file, and the counts in
eval/questions_boston.json were computed against an older one. That is not a bug
in the pipeline — it is the eval set going stale, and the honest fix is to
recompute the answer key, never to loosen the SQL.

This recomputes every ground-truth figure in PANDAS (independently of DuckDB,
so the two agreeing is real evidence), prints old vs new, and rewrites the
numbers in eval/questions_boston.json and eval/prove.py.

  .venv/bin/python -m eval.reverify          # show what would change
  .venv/bin/python -m eval.reverify --write  # apply it
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CSV = REPO / "data" / "downloads" / "311-service-requests.csv"
QUESTIONS = REPO / "eval" / "questions_boston.json"
PROVE = REPO / "eval" / "prove.py"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="apply the patch")
    args = ap.parse_args()

    if not CSV.exists():
        raise SystemExit(f"{CSV} missing — run `make data` first.")
    df = pd.read_csv(CSV, low_memory=False)

    n = len(df)
    dorch = int((df.neighborhood == "Dorchester").sum())
    rodent_all = int((df.type == "Rodent Activity").sum())
    rodent_dorch = int(((df.type == "Rodent Activity") & (df.neighborhood == "Dorchester")).sum())
    open_n = int((df.case_status == "Open").sum())
    closed_n = int((df.case_status == "Closed").sum())
    overdue = int((df.on_time == "OVERDUE").sum())
    ontime = int((df.on_time == "ONTIME").sum())
    dates = pd.to_datetime(df.open_dt, errors="coerce")
    lo, hi = dates.min(), dates.max()
    days = int((hi - lo).days)
    src = df.source.value_counts()
    reason_top = df.reason.value_counts()

    print(f"CSV: {CSV.name}   rows={n:,}   {lo:%Y-%m-%d} .. {hi:%Y-%m-%d}  ({days} days)\n")

    # old value -> new value. Formatted with commas, exactly as they appear in the JSON.
    mapping = {
        "78,526": f"{n:,}",           "78526": str(n),
        "9,935":  f"{dorch:,}",       "9935":  str(dorch),
        "3,535":  f"{rodent_all:,}",  "3535":  str(rodent_all),
        "478":    str(rodent_dorch),
        "38,570": f"{open_n:,}",      "38570": str(open_n),
        "39,956": f"{closed_n:,}",
        "42,797": f"{overdue:,}",     "42797": str(overdue),
        "35,729": f"{ontime:,}",
        "44,284": f"{int(reason_top.iloc[0]):,}",
        "232":    str(days),
        "13.5%":  f"{100*rodent_dorch/rodent_all:.1f}%",
        "55%":    f"{round(100*overdue/(overdue+ontime))}%",
        "August 20, 2026": f"{hi:%B %-d, %Y}",
        "Aug 20, 2026":    f"{hi:%b %-d, %Y}",
        "Aug 20 2026":     f"{hi:%b %-d %Y}",
    }
    for i, name in enumerate(["Employee Generated", "Citizens Connect App", "Constituent Call"]):
        if name in src.index:
            old = ["44,179", "25,122", "8,512"][i]
            mapping[old] = f"{int(src[name]):,}"

    print(f"{'old':>18}  ->  {'new':<12}")
    for old, new in mapping.items():
        flag = "" if old == new else "  <-- changes"
        print(f"{old:>18}  ->  {new:<12}{flag}")

    if not args.write:
        print("\n(dry run — re-run with --write to apply)")
        return

    # longest keys first so "78,526" is never eaten by a shorter overlapping key
    keys = sorted(mapping, key=len, reverse=True)
    for path in (QUESTIONS, PROVE):
        text = path.read_text(encoding="utf-8")
        for old in keys:
            if mapping[old] != old:
                text = text.replace(old, mapping[old])
        path.write_text(text, encoding="utf-8")
        print(f"patched {path.relative_to(REPO)}")
    print("\nNow: make prove   (all 11 should pass)")


if __name__ == "__main__":
    main()
