"""Tables stay tables.

The baseline shreds a CSV into prose, embeds the prose, retrieves whatever
scores well, and asks an 8B model to count. It answered 10 when the truth
was 9 — with all 28 rows sitting in the retrieved context. Counting is not
a retrieval problem and it is not a language problem. It is arithmetic.

So: every CSV in the corpus (and every real Analyze Boston download) is
registered as a DuckDB table. Aggregate questions become SQL. The number in
the answer is computed, and the SQL that computed it is the citation.

  from civic import tables
  tables.answer("How many 311 requests list a location on the bridge?")
  -> ComputedAnswer(value=9, sql='SELECT COUNT(*) ...', rows=[...])
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pandas as pd

from civic import llm

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DOCS = REPO_ROOT / "lab0_boston" / "corpus" / "docs"
DOWNLOADS = REPO_ROOT / "data" / "downloads"
REAL_CSV_ROWS = 200_000  # real datasets: read fully, not the starter's 2_000

CSV_FENCE = re.compile(r"```csv\s*\n(.+?)```", re.S)
SAFE_SQL = re.compile(r"^\s*(?:WITH\b|SELECT\b)", re.I)
FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|COPY|INSTALL|LOAD)\b", re.I)


@dataclass
class ComputedAnswer:
    value: object
    sql: str
    rows: list[dict] = field(default_factory=list)
    table: str = ""
    error: str | None = None

    def as_evidence(self) -> str:
        head = f"[computed via SQL over table `{self.table}`]\n{self.sql}\nresult: {self.value}"
        if self.rows:
            head += "\nrows:\n" + "\n".join(str(r) for r in self.rows[:15])
        return head


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

def _con() -> duckdb.DuckDBPyConnection:
    """A fresh in-memory DB with every available table registered."""
    con = duckdb.connect(":memory:")
    for name, df in _frames().items():
        con.register(name, df)
    return con


_CACHE: dict[str, pd.DataFrame] | None = None


def _frames() -> dict[str, pd.DataFrame]:
    """Every CSV we can see, as {table_name: DataFrame}. Cached per process."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    frames: dict[str, pd.DataFrame] = {}

    # 1. fenced ```csv blocks inside the Fort Point corpus documents
    for path in sorted(CORPUS_DOCS.glob("doc*.md")):
        text = path.read_text(encoding="utf-8")
        for i, block in enumerate(CSV_FENCE.findall(text)):
            try:
                df = pd.read_csv(io.StringIO(block.strip()))
            except Exception:
                continue
            if df.empty:
                continue
            name = _table_name(path.stem, i)
            frames[name] = df

    # 2. real Analyze Boston downloads
    for path in sorted(DOWNLOADS.glob("*.csv")):
        try:
            df = pd.read_csv(path, nrows=REAL_CSV_ROWS, low_memory=False)
        except Exception:
            continue
        name = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_")
        if name[:1].isdigit():
            name = "t" + name  # SQL identifiers cannot start with a digit
        frames[name] = df

    _CACHE = frames
    return frames


def _table_name(stem: str, index: int) -> str:
    """doc01_311_service_request_export_... -> doc01_311_service_request"""
    parts = stem.split("_")
    name = "_".join(parts[:4]).lower()
    return f"{name}_{index}" if index else name


def schema_card() -> str:
    """Compact schema description for the text-to-SQL prompt.

    Sample rows matter more than column names: they teach the model what the
    location strings actually look like, which is the difference between
    LIKE '%bridge%' and a query that returns nothing.
    """
    lines = []
    for name, df in _frames().items():
        cols = ", ".join(f"{c} ({df[c].dtype})" for c in df.columns)
        lines.append(f"TABLE {name}  -- {len(df)} rows\n  columns: {cols}")
        for _, row in df.head(2).iterrows():
            cells = "; ".join(f"{c}={str(v)[:48]}" for c, v in row.items())
            lines.append(f"  sample: {cells}")
    return "\n".join(lines) or "(no tables registered — run `make data`)"


def table_names() -> list[str]:
    return list(_frames())


# --------------------------------------------------------------------------
# text-to-SQL
# --------------------------------------------------------------------------

SQL_PROMPT = """You write DuckDB SQL. Output ONLY a SQL query, no prose, no explanation.

Rules:
- SELECT queries only. Never INSERT/UPDATE/DELETE/CREATE.
- Match text loosely: use LOWER(col) LIKE '%term%' rather than equality.
- For "how many", return a single COUNT(*).
- For durations between dates, use DATE_DIFF('month', a, b) and cast strings
  with CAST(col AS DATE) or STRPTIME as needed.
- Use only the tables and columns listed below.

{schema}

Question: {question}

SQL:"""


def to_sql(question: str) -> str | None:
    raw = llm.complete(SQL_PROMPT.format(schema=schema_card(), question=question),
                       model=llm.SQL_MODEL)
    sql = llm.extract_code(raw, "sql")
    if not sql:
        return None
    sql = sql.rstrip(";").strip()
    if not SAFE_SQL.match(sql) or FORBIDDEN.search(sql):
        return None  # refuse anything that isn't a read
    return sql


def run_sql(sql: str) -> ComputedAnswer:
    try:
        df = _con().execute(sql).fetchdf()
    except Exception as exc:
        return ComputedAnswer(value=None, sql=sql, error=f"{type(exc).__name__}: {exc}")
    rows = df.head(50).to_dict("records")
    value = df.iat[0, 0] if df.shape == (1, 1) else rows
    if hasattr(value, "item"):
        value = value.item()
    return ComputedAnswer(value=value, sql=sql, rows=rows)


def answer(question: str, retries: int = 1) -> ComputedAnswer | None:
    """Question -> SQL -> number. Retries once with the error fed back in."""
    sql = to_sql(question)
    if sql is None:
        return None
    result = run_sql(sql)
    if result.error and retries:
        repair = (f"{SQL_PROMPT.format(schema=schema_card(), question=question)}\n{sql}\n\n"
                  f"That query failed with: {result.error}\nCorrected SQL:")
        fixed = llm.extract_code(llm.complete(repair, model=llm.SQL_MODEL), "sql")
        if fixed and SAFE_SQL.match(fixed) and not FORBIDDEN.search(fixed):
            result = run_sql(fixed.rstrip(";").strip())
    return result


if __name__ == "__main__":  # quick registry inspection: python -m civic.tables
    print(schema_card())
