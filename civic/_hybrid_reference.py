"""Track A: dense-only vs BM25+dense hybrid, side by side.

Dense embeddings are great at "restaurant" ~ "food establishment" but
fumble exact tokens like street names — "Washington St" embeds close to
every other street query. BM25 is the opposite: exact-token matching,
no synonyms. Reciprocal Rank Fusion (RRF) combines both rankings so a
result strong in either list surfaces. This script prints both result
lists for the same query so the difference is visible, not asserted.

Run:  make track-a     (or: python track_a_engine/hybrid_search.py ["query"])
"""
from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

REPO_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = str(REPO_ROOT / ".chroma" / "boston")
COLLECTION = "boston_open_data"
TOP_K = 5
RRF_K = 60  # standard damping constant — rank 0 dominates less


def load_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        return client.get_collection(COLLECTION)
    except Exception:
        raise SystemExit("No Boston collection — run `make data` then `python boston/ingest.py` first.")


def dense_ranking(coll, query: str, k: int) -> list[tuple[str, str]]:
    res = coll.query(query_texts=[query], n_results=k)
    return list(zip(res["ids"][0], res["documents"][0]))


def bm25_ranking(ids: list[str], docs: list[str], query: str, k: int) -> list[tuple[str, str]]:
    bm25 = BM25Okapi([d.lower().split() for d in docs])
    scores = bm25.get_scores(query.lower().split())
    order = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)[:k]
    return [(ids[i], docs[i]) for i in order]


def rrf_fuse(rankings: list[list[tuple[str, str]]], k: int) -> list[tuple[str, str]]:
    scores: dict[str, float] = {}
    text: dict[str, str] = {}
    for ranking in rankings:
        for rank, (doc_id, doc) in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
            text[doc_id] = doc
    top = sorted(scores, key=scores.get, reverse=True)[:k]
    return [(i, text[i]) for i in top]


def show(title: str, ranking: list[tuple[str, str]]) -> None:
    print(f"\n{title}")
    for n, (doc_id, doc) in enumerate(ranking, 1):
        print(f"  {n}. [{doc_id}] {doc[:110].replace(chr(10), ' ')}...")


def main() -> None:
    query = " ".join(sys.argv[1:]) or "rats on Washington St"
    coll = load_collection()
    data = coll.get()  # full corpus for BM25 — fine at lab scale
    dense = dense_ranking(coll, query, TOP_K)
    # BM25 over a wider dense candidate pool would be cheaper at scale;
    # at lab scale we score the whole collection for an honest contrast.
    sparse = bm25_ranking(data["ids"], data["documents"], query, TOP_K)
    hybrid = rrf_fuse([dense, sparse], TOP_K)
    print(f"QUERY: {query!r}")
    show("DENSE ONLY (chroma default embedder)", dense)
    show("BM25 ONLY (exact-token match)", sparse)
    show("HYBRID (Reciprocal Rank Fusion of both)", hybrid)
    print("\nWhere do the lists disagree? That gap is your Track A build space.")


if __name__ == "__main__":
    main()
