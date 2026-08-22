"""LLM-as-judge over the 24 Fort Point questions — for ANY pipeline.

Derived from lab0_millbrook/judge.py in the RAG the City starter repo
(Apache-2.0). One change, and it is the change that matters: the pipeline
under test is a --pipeline argument instead of a hardcoded import, so the
same grader, the same questions and the same corpus score both systems.

  python -m eval.judge                                # baseline
  python -m eval.judge --pipeline civic.pipeline      # ours
  python -m eval.judge --pipeline civic.pipeline --save eval/results/after.txt

Any module exposing retrieve(question, docs_dir=, collection=) and
generate(question, chunks) can be graded.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

QUESTIONS = REPO_ROOT / "lab0_boston" / "questions.json"
DOCS_DIR = REPO_ROOT / "lab0_boston" / "corpus" / "docs"
VERDICTS = ("correct", "partially_correct", "wrong", "fabricated")
POINTS = {"correct": 1.0, "partially_correct": 0.5, "wrong": 0.0, "fabricated": 0.0}

JUDGE_PROMPT = """You are grading a RAG system's answer. Reply with ONE word from:
correct, partially_correct, wrong, fabricated.

Use "fabricated" when the answer confidently states details that appear in
neither the expected answer nor the question (invented facts).
An answer that says the documents do not contain the information, when the
expected answer also says so, is "correct" — not "wrong".

Question: {question}
Expected answer: {expected}
Known wrong answers a RAG might give: {wrong}
System's answer: {answer}

Verdict (one word):"""


def band(pct: float) -> str:
    if pct >= 90:
        return "EXCELLENT (90-100)"
    if pct >= 75:
        return "GOOD (75-89)"
    if pct >= 60:
        return "FAIR (60-74)"
    return "POOR (<60)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pipeline", default="baseline.naive_rag",
                    help="module exposing retrieve()/generate() (default: the naive baseline)")
    ap.add_argument("--questions", type=Path, default=QUESTIONS)
    ap.add_argument("--corpus-dir", type=Path, default=DOCS_DIR)
    ap.add_argument("--collection", default=None,
                    help="chroma collection (default: the pipeline's own)")
    ap.add_argument("--save", type=Path, default=None, help="also write the report here")
    args = ap.parse_args()

    system = importlib.import_module(args.pipeline)
    collection = args.collection or getattr(system, "COLLECTION", "fortpoint_naive")
    questions = json.loads(args.questions.read_text(encoding="utf-8"))

    from civic.llm import complete, first_word
    if complete("Reply with: ok") is None:   # fail fast, not 24 questions later
        raise SystemExit(1)

    lines: list[str] = []

    def emit(text: str = "") -> None:
        print(text)
        lines.append(text)

    emit(f"PIPELINE: {args.pipeline}    COLLECTION: {collection}")
    emit(f"RUN AT:   {datetime.now().isoformat(timespec='seconds')}")
    emit()

    by_cat: dict[str, list[str]] = defaultdict(list)
    fabricated: list[str] = []
    for i, q in enumerate(questions, 1):
        chunks = system.retrieve(q["question"], docs_dir=args.corpus_dir, collection=collection)
        answer = system.generate(q["question"], chunks) or "(no answer)"
        verdict = first_word(
            complete(JUDGE_PROMPT.format(question=q["question"], expected=q["expected_answer"],
                                         wrong="; ".join(q["wrong_answers"]), answer=answer)),
            VERDICTS, default="wrong")
        by_cat[q["category"]].append(verdict)
        if verdict == "fabricated":
            fabricated.append(q["id"])
        emit(f"  [{i:2d}/{len(questions)}] {q['id']:>2} {verdict:<17} {q['question'][:52]}")

    total = sum(POINTS[v] for vs in by_cat.values() for v in vs)
    pct = 100.0 * total / len(questions)
    emit("\nPER-CATEGORY RESULTS")
    for cat, verdicts in sorted(by_cat.items()):
        emit(f"  {cat:<40} {sum(POINTS[v] for v in verdicts):>4.1f} / {len(verdicts)}")
    emit(f"\nTOTAL: {total:.1f} / {len(questions)}  ->  {pct:.0f}%   BAND: {band(pct)}")
    emit(f"FABRICATIONS: {', '.join(fabricated) if fabricated else 'none'}"
         + ("   <-- CRITICAL FAILURE" if fabricated else "   <-- clean"))

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nsaved -> {args.save}")


if __name__ == "__main__":
    main()
