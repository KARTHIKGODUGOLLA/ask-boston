"""Proof, with no model involved, that the computed answers are exact.

Ground truth comes from lab0_boston/DESIGN_NOTES.md, where the corpus authors
counted the 311 export by hand before writing it. Each case below runs fixed
SQL against the same rows the retriever would otherwise have handed to an 8B
model, and compares.

This is the fastest possible signal that the compute path works: no Ollama,
no embeddings, under a second. Run it before anything else, and run it again
after every change to civic/tables.py.

  make prove
"""
from __future__ import annotations

import sys

from civic import tables

# (label, sql, expected, note) — expectations from DESIGN_NOTES.md
CASES = [
    ("Q9A  rows located on the bridge",
     """SELECT COUNT(*) FROM doc01_311_service_request
        WHERE LOWER(location) LIKE '%northern avenue bridge%'""",
     9, "baseline answered 10, and listed ten items to prove it"),

    ("Q9B  non-English submissions",
     """SELECT COUNT(*) FROM doc01_311_service_request
        WHERE submitted_language <> 'English'""",
     7, "3 Spanish + 2 Haitian Creole + 2 Chinese"),

    ("     total rows in the export",
     "SELECT COUNT(*) FROM doc01_311_service_request",
     28, "sanity check: the whole table is registered, not a chunk of it"),

    ("     open cases",
     "SELECT COUNT(*) FROM doc01_311_service_request WHERE status = 'Open'",
     11, "not asked in the eval set — a live-demo question the judges can invent"),

    ("Q3A  FY2027 design & engineering (budget CSV side)",
     """SELECT fy2027_appropriation FROM doc05_operating_budget_extract
        WHERE LOWER(line_item) LIKE '%design & engineering%'""",
     4200000, "the narrative says $3.65M — a correct answer reports both"),
]


def main() -> int:
    registered = tables.table_names()
    if not registered:
        print("No tables registered. Run `make split` first (and `make data` for the real CSVs).")
        return 1
    print(f"tables registered: {', '.join(registered)}\n")

    failures = 0
    for label, sql, expected, note in CASES:
        result = tables.run_sql(" ".join(sql.split()))
        got = result.value
        ok = (got == expected) and result.error is None
        failures += not ok
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}")
        print(f"         expected {expected!r}, computed {got!r}"
              + (f"  ({result.error})" if result.error else ""))
        print(f"         {note}\n")

    print("-" * 66)
    if failures:
        print(f"{failures} of {len(CASES)} computed answers are wrong — fix civic/tables.py")
    else:
        print(f"All {len(CASES)} computed answers exact. No model was involved, and")
        print("that is the point: these numbers cannot drift, hallucinate, or")
        print("miscount. Retrieval fetches text; counting is computation.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
