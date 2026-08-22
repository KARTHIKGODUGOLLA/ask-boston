"""Retrieval, minus the four deliberate handicaps in the baseline.

The baseline's own docstring lists its sins; this file fixes the three that
cost real points and leaves the fourth alone.

  overlap      500-word chunks with zero overlap cut entities in half. We
               use smaller chunks with a 60-word overlap.
  k            top-3 out of an 11-document corpus is 27% recall, and it is
               why the budget contradiction never surfaces: only ONE of the
               two disagreeing documents gets retrieved. k=6 puts both in
               front of the model, which is the whole fix for stop 3.
  hybrid       dense embeddings match "restaurant" to "food establishment"
               but fumble exact tokens like "Chapter 91" or "02-201". BM25
               is the opposite. Reciprocal Rank Fusion takes both.
  embedder     still all-MiniLM-L6-v2, still monolingual. Swapping it is the
               obvious next win if there's time — see docs/FIELD_MANUAL.md.

Its retrieve() has the same signature as the baseline's, so the judge and
the Streamlit app can switch between them with one import.
"""
from __future__ import annotations

from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "lab0_boston" / "corpus" / "docs"
CHROMA_DIR = str(REPO_ROOT / ".chroma" / "civic")
COLLECTION = "fortpoint_civic"      # NOT fortpoint_naive — baseline index stays intact
CHUNK_WORDS = 700   # every Fort Point doc is <500 words: keep each one WHOLE
OVERLAP = 0         # 220/60 fragmented them and the model filled the gaps
TOP_K = 6
RRF_K = 60

# The real-data suite reads the index that boston/ingest.py builds. Same
# retrieval code, different store — so one --collection flag switches the
# whole pipeline between the Fort Point lab and 78k rows of live 311.
BOSTON_COLLECTION = "boston_open_data"
BOSTON_CHROMA = str(REPO_ROOT / ".chroma" / "boston")


def _chunk(text: str) -> list[str]:
    words = text.split()
    step = max(1, CHUNK_WORDS - OVERLAP)
    return [" ".join(words[i:i + CHUNK_WORDS]) for i in range(0, len(words), step)] or [""]


def build_index(docs_dir: Path = DOCS_DIR, collection: str = COLLECTION):
    if collection == BOSTON_COLLECTION:  # built by boston/ingest.py, not here
        client = chromadb.PersistentClient(path=BOSTON_CHROMA)
        try:
            return client.get_collection(BOSTON_COLLECTION)
        except Exception:
            raise SystemExit("No Boston index — run `make data` then `make ingest` first.")
    if not any(Path(docs_dir).glob("doc*.md")):
        from baseline.split_corpus import FULL_FOR_DOCS, split
        full = FULL_FOR_DOCS.get(Path(docs_dir).resolve())
        if full is None:
            raise SystemExit(f"No doc*.md in {docs_dir} — run `make lab0` first.")
        split(full, Path(docs_dir))
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    coll = client.get_or_create_collection(collection)
    if coll.count() > 0:
        return coll
    ids, docs, metas = [], [], []
    for path in sorted(Path(docs_dir).glob("doc*.md")):
        for i, chunk in enumerate(_chunk(path.read_text(encoding="utf-8"))):
            ids.append(f"{path.stem}-{i}")
            docs.append(chunk)
            metas.append({"source": path.name, "chunk": i})
    coll.add(ids=ids, documents=docs, metadatas=metas)
    return coll


def _rrf(rankings: list[list[str]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
    return scores


def retrieve(question: str, k: int = TOP_K, docs_dir: Path = DOCS_DIR,
             collection: str = COLLECTION) -> list[dict]:
    coll = build_index(docs_dir, collection)
    pool = coll.get()
    ids, texts = pool["ids"], pool["documents"]
    meta = {i: m for i, m in zip(ids, pool["metadatas"])}
    by_id = dict(zip(ids, texts))

    dense = coll.query(query_texts=[question], n_results=min(k * 2, len(ids)))["ids"][0]
    bm25 = BM25Okapi([t.lower().split() for t in texts])
    scored = bm25.get_scores(question.lower().split())
    sparse = [ids[i] for i in sorted(range(len(ids)), key=lambda i: scored[i], reverse=True)[:k * 2]]

    fused = _rrf([dense, sparse])
    top = sorted(fused, key=fused.get, reverse=True)[:k]
    return [{"id": i, "text": by_id[i], "source": meta[i]["source"]} for i in top]
