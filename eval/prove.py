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

# The real 311 export. Ground truth from eval/questions_boston.json, each entry
# there carrying the pandas expression that produced it. These run only if the
# CSV has been downloaded, and they are pinned to THAT download — see the
# scope note below.
REAL_CASES = [
    ("A1   requests filed in Dorchester",
     """SELECT COUNT(*) FROM t311 WHERE neighborhood = 'Dorchester'""",
     9935, "the highest of any neighborhood in this export"),

    ("A2   rodent reports in Dorchester",
     """SELECT COUNT(*) FROM t311
        WHERE type = 'Rodent Activity' AND neighborhood = 'Dorchester'""",
     478, "against 3,535 citywide — about 13.5%"),

    ("A2b  rodent reports citywide",
     "SELECT COUNT(*) FROM t311 WHERE type = 'Rodent Activity'",
     3535, ""),

    ("A3   open cases",
     "SELECT COUNT(*) FROM t311 WHERE case_status = 'Open'",
     38570, "against 39,956 closed"),

    ("C1   rows in the export",
     "SELECT COUNT(*) FROM t311",
     78526, "a partial-year extract — Jan 1 to Aug 20 2026, not an annual total"),

    ("T2   cases missing their SLA target",
     "SELECT COUNT(*) FROM t311 WHERE on_time = 'OVERDUE'",
     42797, "against 35,729 ONTIME — a majority miss"),
]


def _real_table() -> str | None:
    """The registered name of the 311 download, if it has been fetched."""
    for name in tables.table_names():
        if "311" in name and "doc" not in name:
            return name
    return None


def _run(cases, rename: str | None = None) -> int:
    failures = 0
    for label, sql, expected, note in cases:
        sql = " ".join(sql.split())
        if rename:
            sql = sql.replace("t311", rename)
        result = tables.run_sql(sql)
        got = result.value
        ok = (got == expected) and result.error is None
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        print(f"         expected {expected!r}, computed {got!r}"
              + (f"  ({result.error})" if result.error else ""))
        if note:
            print(f"         {note}")
        print()
    return failures


def main() -> int:
    registered = tables.table_names()
    if not registered:
        print("No tables registered. Run `make split` first (and `make data` for the real CSVs).")
        return 1
    print(f"tables registered: {', '.join(registered)}\n")

    print("FORT POINT CORPUS\n")
    failures = _run(CASES)

    total = len(CASES)
    real = _real_table()
    if real is None:
        print("-" * 66)
        print("Real 311 export not downloaded — skipping the live-data cases.")
        print("Run `make data` to include them.\n")
    else:
        print("-" * 66)
        print(f"REAL DATA — {real}\n")
        failures += _run(REAL_CASES, rename=real)
        total += len(REAL_CASES)

    print("-" * 66)
    if failures:
        print(f"{failures} of {total} computed answers are wrong.")
        if real:
            print("If only the REAL DATA cases fail, the CSV has been re-downloaded and")
            print("grown since the ground truth was verified. Re-verify the counts in")
            print("pandas and update eval/questions_boston.json — do not 'fix' the SQL.")
    else:
        print(f"All {total} computed answers exact. No model was involved, and")
        print("that is the point: these numbers cannot drift, hallucinate, or")
        print("miscount. Retrieval fetches text; counting is computation.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
