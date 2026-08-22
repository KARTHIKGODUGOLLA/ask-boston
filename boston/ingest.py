"""Chunk-and-embed the downloaded Boston CSVs into a chroma collection.

The --strategy flag exists to start the chunking-strategies argument
your team should be having:
  * row    — one chunk per CSV row. Precise citations, but a question
             like "what's the worst street for rodents?" needs evidence
             spread over hundreds of rows the retriever can't gather.
  * group  — GROUP_SIZE rows per chunk. More context per hit, fuzzier
             citations. Neither is "right" — that's the point.

Run:  python boston/ingest.py [--strategy row|group] [--limit 2000]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import chromadb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = REPO_ROOT / "data" / "downloads"
CHROMA_DIR = str(REPO_ROOT / ".chroma" / "boston")
COLLECTION = "boston_open_data"
GROUP_SIZE = 20


def row_text(row: pd.Series) -> str:
    # "column: value" per cell keeps the column names in the embedding —
    # raw comma-joined values embed as noise.
    return "; ".join(f"{c}: {v}" for c, v in row.items() if pd.notna(v) and str(v).strip())


def ingest(strategy: str, limit: int) -> None:
    csvs = sorted(DOWNLOADS.glob("*.csv"))
    if not csvs:
        raise SystemExit(f"No CSVs in {DOWNLOADS} — run `make data` first.")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:  # rebuild from scratch so --strategy switches cleanly
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    coll = client.create_collection(COLLECTION)
    for csv in csvs:
        dataset = csv.stem
        df = pd.read_csv(csv, nrows=limit, low_memory=False)
        ids, docs, metas = [], [], []
        if strategy == "row":
            for idx, row in df.iterrows():
                ids.append(f"{dataset}-row{idx}")
                docs.append(row_text(row))
                metas.append({"dataset": dataset, "rows": str(idx)})
        else:  # group
            for start in range(0, len(df), GROUP_SIZE):
                block = df.iloc[start:start + GROUP_SIZE]
                ids.append(f"{dataset}-rows{start}-{start + len(block) - 1}")
                docs.append("\n".join(row_text(r) for _, r in block.iterrows()))
                metas.append({"dataset": dataset, "rows": f"{start}-{start + len(block) - 1}"})
        print(f"  {dataset}: {len(df)} rows -> {len(docs)} chunks (strategy={strategy})")
        for i in range(0, len(docs), 500):  # chroma add() batches
            coll.add(ids=ids[i:i + 500], documents=docs[i:i + 500], metadatas=metas[i:i + 500])
    print(f"Collection '{COLLECTION}' ready at {CHROMA_DIR} — try: python boston/query.py \"...\"")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strategy", choices=["row", "group"], default="row")
    ap.add_argument("--limit", type=int, default=2000, help="rows per CSV (keep laptops alive)")
    args = ap.parse_args()
    ingest(args.strategy, args.limit)


if __name__ == "__main__":
    main()
