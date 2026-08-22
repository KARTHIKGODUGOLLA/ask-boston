"""Decide what kind of question this is, before answering it.

Three routes, because three different machines are needed:

  aggregate  counting, totals, averages, "which is most"  -> SQL over DuckDB
  temporal   elapsed time, durations, "how long since"    -> retrieve, then
                                                             subtract dates
                                                             in Python
  lookup     everything else                              -> retrieval

The label is logged on every answer. During the demo it is the visible proof
that the system chose a strategy instead of throwing one prompt at everything.

A regex prefilter runs first: it is deterministic, instant, and right about
most civic questions. The model is only consulted when the regexes disagree
with each other or match nothing, which keeps the common path fast.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from civic import llm

ROUTES = ("aggregate", "temporal", "lookup")

AGGREGATE_RE = re.compile(
    r"\b(how many|how much .*(total|combined)|number of|count of|count the|total number"
    r"|average|mean |median|most common|least common|which .* (most|fewest|highest|lowest)"
    r"|top \d+|percentage of|what share)\b", re.I)

TEMPORAL_RE = re.compile(
    r"\b(how long|how old|elapsed|duration|since when|for how many years"
    r"|how many years (has|have|had)|been (running|closed|open|operating)"
    r"|getting (better|worse)|over the (last|past) \w+ (year|month))\b", re.I)


@dataclass
class Route:
    label: str
    why: str

    def __str__(self) -> str:
        return f"{self.label} ({self.why})"


LLM_PROMPT = """Classify the question into exactly one category.

aggregate - answering it requires counting rows, summing, averaging, or ranking
temporal  - answering it requires computing an elapsed time or a trend over dates
lookup    - answering it requires finding and reading a passage

Question: {question}

Reply with one word only:"""


def route(question: str) -> Route:
    agg, tmp = bool(AGGREGATE_RE.search(question)), bool(TEMPORAL_RE.search(question))
    if agg and not tmp:
        return Route("aggregate", "matched aggregate phrasing")
    if tmp and not agg:
        return Route("temporal", "matched duration phrasing")
    # ambiguous ("how many years has it been closed") or no signal — ask the model
    label = llm.first_word(llm.complete(LLM_PROMPT.format(question=question)),
                           ROUTES, default="temporal" if tmp else "lookup")
    return Route(label, "classified by model")


if __name__ == "__main__":  # python -m civic.router "question"
    import sys
    q = " ".join(sys.argv[1:]) or "How many 311 requests list a location on the bridge?"
    print(f"{q}\n  -> {route(q)}")
