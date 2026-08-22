"""Build the frozen control-group index. Run ONCE, then never again.

  make freeze-baseline              # LIMIT=2000, matching `make ingest`
  make freeze-baseline LIMIT=20000  # if you raise ingest's limit, raise this too

Naive on purpose and frozen on purpose: one chunk per CSV row, chroma's default
embedder, no metadata beyond dataset+row. Every point we score is the gap
between this index and ours, so it has to stay exactly as broken as it is now.

If you rebuild it after improving the pipeline, you have contaminated the
control group and the before/after number means nothing.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import chromadb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = REPO_ROOT / "data" / "downloads"
CHROMA_DIR = str(REPO_ROOT / ".chroma" / "baseline")
COLLECTION = "baseline_frozen"
STAMP = REPO_ROOT / ".chroma" / "baseline" / "FROZEN_AT.txt"


def row_text(row: pd.Series) -> str:
    return "; ".join(f"{c}: {v}" for c, v in row.items() if pd.notna(v) and str(v).strip())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=2000,
                    help="rows per CSV — MUST match boston/ingest.py's limit")
    ap.add_argument("--force", action="store_true", help="re-freeze anyway (you should not)")
    args = ap.parse_args()

    if STAMP.exists() and not args.force:
        raise SystemExit(
            f"Baseline already frozen:\n  {STAMP.read_text().strip()}\n"
            "This is the control group. Re-freezing after improving the pipeline\n"
            "contaminates the comparison. Pass --force only if the DATA changed.")

    csvs = sorted(DOWNLOADS.glob("*.csv"))
    if not csvs:
        raise SystemExit(f"No CSVs in {DOWNLOADS} — run `make data` first.")

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    coll = client.create_collection(COLLECTION)

    lines = []
    for csv in csvs:
        df = pd.read_csv(csv, nrows=args.limit, low_memory=False)
        ids = [f"{csv.stem}-row{i}" for i in df.index]
        docs = [row_text(r) for _, r in df.iterrows()]
        metas = [{"dataset": csv.stem, "rows": str(i)} for i in df.index]
        for i in range(0, len(docs), 500):
            coll.add(ids=ids[i:i + 500], documents=docs[i:i + 500], metadatas=metas[i:i + 500])
        line = f"{csv.name}: {len(df)} rows (limit={args.limit})"
        print(f"  {line}")
        lines.append(line)

    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.write_text("frozen with limit=%d\n%s\n" % (args.limit, "\n".join(lines)), encoding="utf-8")
    print(f"\nFrozen -> {CHROMA_DIR} ({COLLECTION}). Do not rebuild this.")


if __name__ == "__main__":
    main()
