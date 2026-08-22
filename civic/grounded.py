"""The gate every answer passes through before a citizen sees it.

The rubric's top anchor is "says 'I don't know' instead of guessing", and
fabrication is an automatic critical failure. The baseline fails this three
times out of twenty-four, and it fails in the most dangerous way available:
fluently. Question 4B asks what Wilner Joseph did for work before 2021. The
corpus deliberately does not say. The baseline says something anyway.

Two checks, cheapest first:

  1. numeric audit (free, deterministic) — every number the answer states
     must appear in the evidence, or have been computed by civic.tables /
     civic.temporal. A number from nowhere is the signature of a fabrication.
  2. claim audit (one model call) — is every statement supported?

Fail either and the answer is replaced by an honest abstention. Refusing is
a feature here, not an error path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from civic import llm

ABSTENTION = ("I don't know — the available records don't say. "
              "Here is what they do contain:")

NUM_RE = re.compile(r"\d[\d,]*\.?\d*")

VERIFY_PROMPT = """You are auditing an answer for fabrication. Be strict.

EVIDENCE:
{evidence}

QUESTION: {question}
ANSWER: {answer}

Is every factual claim in the ANSWER directly supported by the EVIDENCE?
An answer that says the records don't contain something is SUPPORTED.
An answer that adds a cause, a reason, a job, a date, or a number not in the
evidence is UNSUPPORTED.

Reply with exactly one word: supported or unsupported"""


@dataclass
class Verdict:
    ok: bool
    reason: str
    stray_numbers: list[str]


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in NUM_RE.findall(text or "")}


def audit(question: str, answer: str, evidence: str,
          computed: str | None = None) -> Verdict:
    """Cheap deterministic check first, model call only if that passes."""
    allowed = _numbers(evidence) | _numbers(computed or "")
    stray = sorted(n for n in _numbers(answer) - allowed if len(n) > 1)
    if stray:
        return Verdict(False, f"states number(s) absent from the evidence: {', '.join(stray)}", stray)
    label = llm.first_word(
        llm.complete(VERIFY_PROMPT.format(evidence=evidence, question=question, answer=answer)),
        ("unsupported", "supported"), default="supported")
    return Verdict(label == "supported",
                   "model audit: unsupported claim" if label != "supported" else "supported", [])


def abstain(evidence_summary: str) -> str:
    return f"{ABSTENTION}\n{evidence_summary}"
