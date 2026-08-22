"""ask-boston: route, compute, then refuse to guess.

  question
     |
  router.route()
     |
     +-- aggregate --> tables.answer()      SQL over DuckDB; the number is computed
     +-- temporal  --> temporal.compute()   dates extracted, subtraction in Python
     +-- lookup    --> retrieval.retrieve() hybrid BM25 + dense, k=6
     |
  synthesize (one call, evidence only)
     |
  grounded.audit() --> pass: answer with citations
                   \-> fail: honest abstention

retrieve() and generate() keep the baseline's signatures on purpose, so
eval/judge.py --pipeline civic.pipeline swaps systems without touching the
questions, the corpus, or the grader.

  python -m civic.pipeline "How many 311 requests list a location on the bridge?"
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from civic import grounded, retrieval, router, tables, temporal
from civic.llm import complete

DOCS_DIR = retrieval.DOCS_DIR
COLLECTION = retrieval.COLLECTION

ANSWER_PROMPT = """Answer the question using ONLY the evidence below.

Rules:
- If the evidence does not contain the answer, say so plainly. Do not guess a
  cause, a reason, or a number.
- If two sources give different figures for the same thing, report BOTH and
  say they disagree. Never average them or pick one silently.
- Any number marked [computed] is already correct — restate it exactly.
- Be brief. Two or three sentences.

Evidence:
{evidence}

Question: {question}
Answer:"""


@dataclass
class Answer:
    text: str
    route: str = "lookup"
    sources: list[str] = field(default_factory=list)
    sql: str | None = None
    computed: str | None = None
    abstained: bool = False
    audit_note: str = ""

    def __str__(self) -> str:
        return self.text


# -- baseline-compatible surface -------------------------------------------

def retrieve(question: str, k: int = retrieval.TOP_K, docs_dir: Path = DOCS_DIR,
             collection: str = COLLECTION) -> list[dict]:
    return retrieval.retrieve(question, k=k, docs_dir=docs_dir, collection=collection)


def generate(question: str, chunks: list[dict]) -> str | None:
    """Same signature as baseline.naive_rag.generate — the judge calls this."""
    result = respond(question, chunks)
    return result.text if result else None


# -- the real entry point ---------------------------------------------------

def respond(question: str, chunks: list[dict] | None = None) -> Answer:
    chunks = chunks if chunks is not None else retrieve(question)
    decision = router.route(question)
    passages = "\n\n---\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)
    sources = sorted({c["source"] for c in chunks})
    computed: str | None = None
    sql: str | None = None

    if decision.label == "aggregate":
        result = tables.answer(question)
        if result and result.error is None and result.value is not None:
            computed, sql = result.as_evidence(), result.sql
        # no usable SQL -> fall through to retrieval, but the gate still applies

    elif decision.label == "temporal":
        duration = temporal.compute(question, chunks)
        if duration is not None:
            computed = duration.as_evidence()

    evidence = f"{computed}\n\n---\n\n{passages}" if computed else passages
    draft = complete(ANSWER_PROMPT.format(evidence=evidence, question=question))
    if draft is None:
        return Answer("(no answer — model offline)", decision.label, sources, sql, computed)

    verdict = grounded.audit(question, draft, passages, computed)
    if not verdict.ok:
        summary = "; ".join(sources) or "no matching records"
        return Answer(grounded.abstain(f"Records consulted: {summary}."),
                      decision.label, sources, sql, computed,
                      abstained=True, audit_note=verdict.reason)
    return Answer(draft, decision.label, sources, sql, computed, audit_note=verdict.reason)


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        raise SystemExit('Usage: python -m civic.pipeline "your question"')
    result = respond(question)
    print(f"\nQ: {question}")
    print(f"-- route: {result.route}")
    if result.sql:
        print(f"-- sql:   {result.sql}")
    if result.abstained:
        print(f"-- gate:  ABSTAINED ({result.audit_note})")
    print("-- answer " + "-" * 48)
    print(result.text)
    print("\nSOURCES: " + (", ".join(result.sources) or "—"))


if __name__ == "__main__":
    main()
