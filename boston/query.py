"""Grounded-answer CLI over the Boston collection, with citations.

Every answer cites dataset + row ids from chunk metadata, and the
prompt orders the model to abstain when the context doesn't contain
the answer — the Track B rubric anchor is "says 'I don't know'
instead of guessing."

Run:  python boston/query.py "Show 311 complaints on Washington St"
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import chromadb

REPO_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = str(REPO_ROOT / ".chroma" / "boston")
COLLECTION = "boston_open_data"
TOP_K = 5
MODEL = os.environ.get("OLLAMA_MODEL", "granite3.1-dense:8b")

PROMPT = (
    "You answer questions about Boston open data using ONLY the context.\n"
    "If the context does not contain the answer, say \"I don't know — the\n"
    "data doesn't say\" rather than guessing.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\nAnswer:"
)


def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        coll = client.get_collection(COLLECTION)
    except Exception:
        raise SystemExit("No Boston collection yet — run `make data` then `python boston/ingest.py`.")
    res = coll.query(query_texts=[question], n_results=k)
    return [
        {"text": d, "dataset": m["dataset"], "rows": m["rows"]}
        for d, m in zip(res["documents"][0], res["metadatas"][0])
    ]


def answer(question: str, chunks: list[dict]) -> str | None:
    context = "\n\n".join(f"[{c['dataset']} rows {c['rows']}]\n{c['text']}" for c in chunks)
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=MODEL, temperature=0)
        return llm.invoke(PROMPT.format(context=context, question=question)).content.strip()
    except Exception as exc:
        print(f"[!] Ollama unreachable ({type(exc).__name__}) — showing retrieval only.", file=sys.stderr)
        print(f"[!] Fix: ollama serve && ollama pull {MODEL}", file=sys.stderr)
        return None


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python boston/query.py "your question"')
    question = " ".join(sys.argv[1:])
    chunks = retrieve(question)
    result = answer(question, chunks)
    if result is not None:
        print(result)
    print("\nCITATIONS")
    for c in chunks:
        print(f"  - {c['dataset']} (rows {c['rows']})")


if __name__ == "__main__":
    main()
