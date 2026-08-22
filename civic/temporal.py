"""Durations are computed, never recalled.

Lab 0 stop 2 and question 2B are the same failure: the elapsed time is
written in no document, so the model invents one. "How long has Yolanda been
running the bakery?" needs March 2011 from one document and a June 2026
anchor from another, then subtraction — and if it grabs the wrong closure
date it confidently reports 29 years instead of 11.

So we do it in two explicit halves. The model's only job is to read dates out
of retrieved text and say what each one means. Python does the arithmetic,
and refuses when a date is missing rather than guessing at one.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date

from civic import llm

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}

EXTRACT_PROMPT = """From the context below, extract every date that is relevant to this question.

Question: {question}

Context:
{context}

Reply with ONLY a JSON array. Each item: {{"date": "YYYY-MM" or "YYYY", "means": "<short description>", "source": "<document filename>"}}
If the context contains no relevant date, reply with []

JSON:"""

PICK_PROMPT = """To answer the question, which TWO of these dates must be subtracted?

Question: {question}

Dates:
{dates}

Reply with ONLY two indices as JSON, earliest first: [i, j]
If no pair of these dates answers the question, reply with []

JSON:"""


@dataclass
class Duration:
    start: date
    end: date
    months: int
    start_means: str
    end_means: str
    sources: list[str]

    @property
    def years(self) -> float:
        return round(self.months / 12, 1)

    def phrase(self) -> str:
        y, m = divmod(self.months, 12)
        if y and m:
            return f"about {y} years and {m} months"
        return f"about {y} years" if y else f"about {m} months"

    def as_evidence(self) -> str:
        return (f"[computed] {self.start.isoformat()[:7]} ({self.start_means}) -> "
                f"{self.end.isoformat()[:7]} ({self.end_means}) = {self.months} months "
                f"= {self.phrase()}\nsources: {', '.join(sorted(set(self.sources)))}")


def _parse(value: str) -> date | None:
    value = str(value).strip()
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", value):
        return date(int(m[1]), int(m[2]), int(m[3] or 1))
    if m := re.fullmatch(r"(\d{4})", value):
        return date(int(m[1]), 1, 1)
    if m := re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", value):
        if (mm := MONTHS.get(m[1].lower())):
            return date(int(m[2]), mm, 1)
    return None


def _json(raw: str | None, default):
    if not raw:
        return default
    m = re.search(r"[\[{].*[\]}]", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else default
    except Exception:
        return default


def extract_dates(question: str, chunks: list[dict]) -> list[dict]:
    context = "\n\n---\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks)
    items = _json(llm.complete(EXTRACT_PROMPT.format(question=question, context=context)), [])
    out = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict) and (d := _parse(item.get("date", ""))):
            out.append({"date": d, "means": item.get("means", ""), "source": item.get("source", "")})
    return out


def compute(question: str, chunks: list[dict]) -> Duration | None:
    """Returns a Duration, or None — and None means 'say so', not 'guess'."""
    dates = extract_dates(question, chunks)
    if len(dates) < 2:
        return None
    listing = "\n".join(f"  [{i}] {d['date'].isoformat()[:7]} — {d['means']}"
                        for i, d in enumerate(dates))
    pick = _json(llm.complete(PICK_PROMPT.format(question=question, dates=listing)), [])
    if not (isinstance(pick, list) and len(pick) == 2):
        return None
    try:
        a, b = dates[int(pick[0])], dates[int(pick[1])]
    except (ValueError, TypeError, IndexError):
        return None
    if a["date"] > b["date"]:
        a, b = b, a
    months = (b["date"].year - a["date"].year) * 12 + (b["date"].month - a["date"].month)
    if months <= 0:
        return None
    return Duration(a["date"], b["date"], months, a["means"], b["means"],
                    [a["source"], b["source"]])
