"""The naive control group, pointed at the real Boston CSVs.

`baseline/naive_rag.py` is the starter's Lab 0 baseline over the Fort Point
documents. This is the same naivety over `.chroma/baseline` — the FROZEN index
that `make freeze-baseline` builds once and nobody rebuilds.

Two indexes exist on purpose. `boston/ingest.py` deletes and recreates its
collection on every run, so if the control group read from the same store,
then the moment we improved chunking the baseline would improve too — and
since most of our gain comes from ingestion, we would be handing our best work
to the control group and measuring almost nothing.

**Fairness rule:** both sides must index the same rows. If you change `LIMIT`
for `make ingest`, re-freeze with the same value or the comparison is worthless
and a judge will say so.

Deliberately naive, exactly like the Lab 0 baseline: dense-only, top-3, no
reranking, no metadata filters, no aggregation, no abstention, one LLM call.

  python -m eval.judge --pipeline baseline.naive_boston --collection baseline_frozen
"""
from __future__ import annotations

import sys
from pathlib import Path

import chromadb

REPO_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = str(REPO_ROOT / ".chroma" / "baseline")
COLLECTION = "baseline_frozen"
TOP_K = 3

PROMPT = (
    "Answer the question using ONLY the context below.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\nAnswer:"
)


def retrieve(question: str, k: int = TOP_K, docs_dir: Path | None = None,
             collection: str = COLLECTION) -> list[dict]:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        coll = client.get_collection(collection)
    except Exception:
        raise SystemExit(
            "No frozen baseline index — build it ONCE with `make freeze-baseline`.\n"
            "It is the control group. Never rebuild it after that.")
    res = coll.query(query_texts=[question], n_results=k)
    return [
        {"id": i, "text": d, "source": f"{m.get('dataset', '?')} rows {m.get('rows', '?')}"}
        for i, d, m in zip(res["ids"][0], res["documents"][0], res["metadatas"][0])
    ]


def generate(question: str, chunks: list[dict]) -> str | None:
    from civic.llm import complete
    context = "\n\n---\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)
    return complete(PROMPT.format(context=context, question=question))


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        raise SystemExit('Usage: python -m baseline.naive_boston "your question"')
    chunks = retrieve(question)
    print(f"\nQ: {question}\n-- retrieved top {len(chunks)} " + "-" * 30)
    for n, c in enumerate(chunks, 1):
        print(f"  [{n}] {c['source']} :: {c['text'][:180]}...")
    print("-- answer " + "-" * 48)
    print(generate(question, chunks) or "(model offline)")


if __name__ == "__main__":
    main()
