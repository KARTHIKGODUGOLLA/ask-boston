# Fort Point Field Manual — rag-the-city-starter teardown

Working notes for RAG the City, Aug 22 2026. Baseline run: **21/24 = 88% GOOD, 3 fabrications (2B, 4B, 9A) = CRITICAL FAILURE.**

---

## 00 · Read this first

**The 88% is not the story. The three fabrications are.** The rubric makes fabrication an automatic
critical failure. 88% with three invented answers loses to 80% with zero.

The three that failed are not random:

| id | Category | What it really needs |
|----|----------|----------------------|
| 2B | Temporal Complexity | Date arithmetic — March 2011 → mid-2026 ≈ 15 years, written in no document |
| 4B | Missing Context | Abstention — Wilner's pre-2021 job is deliberately absent from the corpus |
| 9A | Aggregation & Counting | Counting — 9 of 28 rows; the model said 10 and listed them |

All three are one defect: **the model was asked to compute and improvised instead.** One idea —
*route computation to code, gate everything else on evidence* — kills all three. That's the thesis,
the build, and the 2-minute demo.

### The finding that sharpens the pitch

Every one of the 11 Fort Point docs is **under 500 words, so each is exactly one chunk.** Nothing is
ever cut at a boundary. On 9A the entire 28-row CSV was retrieved intact as chunk #1 and the model
still said 10. The tour's "rows lost at chunk boundaries" story is *not* what happened here.
Counting failed because an 8B model can't count 28 rows. Provable in one screenshot.

---

## 01 · The repo in pipeline order

Folders are organized by edition, not architecture. Read in data-flow order:

1. **`Makefile`** (50 ln) — the whole API surface. Every target is one `python -m` call with explicit
   flags. `make help` lists them.
2. **`lab0_millbrook/split_corpus.py`** — ingestion. Splits `fortpoint_full.md` into 11 `doc*.md`.
   Pure text surgery, no RAG.
3. **`lab0_millbrook/naive_rag.py`** (137 ln) — **the most important file.** The entire pipeline.
   `_chunk` (500 whitespace words, no overlap) → `build_index` (Chroma, default MiniLM) →
   `retrieve` (top-3, no rerank, no filters) → `generate` (one Ollama call, temp 0). Everything you
   build tomorrow replaces or wraps these four.
4. **`lab0_boston/questions.json` + `tour_stops.json`** — 24 eval records
   `{id, category, difficulty, question, expected_answer, wrong_answers}`. The `wrong_answers` array
   is pre-written distractors the judge uses.
5. **`lab0_boston/DESIGN_NOTES.md`** — **the answer key.** Cast, timeline invariants, hand-counted 311
   ground truth (9 bridge rows, 7 non-English), question→evidence table for all 24, and which
   questions are deliberately unanswerable. Read it; never index it.
6. **`lab0_millbrook/judge.py`** — LLM-as-judge. Verdicts correct / partially_correct / wrong /
   fabricated. `correct=1.0`, `partial=0.5`. Bands: EXCELLENT ≥90, GOOD ≥75, FAIR ≥60.
7. **`boston/download.py → ingest.py → query.py`** — the real-data pipeline; **this is what you ship.**
   CKAN-resolved downloads; `--strategy row|group` chunking; grounded CLI with citations and an
   abstention instruction already in the prompt.
8. **`track_a_engine/`** — `hybrid_search.py` works (BM25 + dense, RRF fused, all three rankings
   printed). `multi_source.py` and `eval_ragas.py` are TODO stubs.
9. **`track_b_experience/app_streamlit.py`** (62 ln) — wraps `boston/query.py`. Renders abstention as a
   green success banner, not an error. Steal this even in Track A.

---

## 02 · The data, and why

### Layer 1 — Fort Point corpus (fiction, 11 docs, 3,075 words)

| doc | Genre | Mimics | Plants |
|-----|-------|--------|--------|
| 01 | 311 export, 28 rows | BOS:311 export | Counting (9/28), multilingual (7 non-English) |
| 02 | Bio dossiers | — | Two Fitzgeralds, two Peñas; the gap in Wilner's history |
| 03 | Council minutes | City Council minutes | "C. Peña"; the 4–0 vote and recusal |
| 04 | Inspection report | Food Establishment Inspections | Violation codes, no cause → abstention |
| 05/06 | Budget CSV + narrative | Operating Budget (published as both) | $4,200,000 vs $3.65M on one line |
| 07 | Roundtable transcript | — | Spanish / Haitian Creole / Chinese; interpreter drops detail |
| 08 | Property & permit record | Property Assessment + Permits | Graph edges: owner, parcel, Ch. 91 license |
| 09 | Newspaper article | — | 30 months vs "two years"; $95M vs $110M |
| 10 | Engineering assessment | — | Domain terms: PE, NBI rating 2 on 0–9 |
| 11 | Personal diary | — | Date anchor for temporal math; family links |

### Layer 2 — real datasets (`make data`)

Only two are auto-fetched:

- **311 Service Requests** — 100K+ rows/yr, genuinely arrives in Spanish/Haitian Creole/Chinese.
  Aggregation playground and multilingual playground at once.
- **Food Establishment Inspections** — abstention playground. Coded violations, no narrative reasons.

Resolved live via `data.boston.gov/api/3/action/package_show`, not hardcoded GUIDs.
**Note:** `multi_source.py` expects `operating-budget.csv`, which `make data` does *not* fetch. Add
the slug to `DATASETS` in `download.py` or grab it by hand.

---

## 03 · Eval commands, and how much to trust them

```
make lab0                 # split corpus + 6-stop narrated tour
make lab0-ask Q="..."     # one question, chunks shown before the answer
make lab0-score           # all 24 → LLM judge → per-category + band
make lab0-millbrook{,-ask,-score}   # the original 22-question challenge
make track-a              # dense vs BM25 vs RRF hybrid, side by side
make track-b              # Streamlit UI
```

Three things about the judge before you optimize against it:

- **It is lenient.** The guide predicts FAIR for naive baselines; you got 88%. Granite grading Granite
  is a soft grader. Check verdicts by hand against `DESIGN_NOTES.md`.
- **It is hardcoded to the baseline.** `judge.py:28` is `from lab0_millbrook import naive_rag`, and
  lines 91–92 call `naive_rag.retrieve/generate` directly. Point it at your pipeline or you'll spend
  the afternoon proudly re-scoring the baseline.
- **It drifts.** Same run twice can differ a point or two. Save your before-number to a file with a
  timestamp tomorrow morning.

Also broken: `track_a_engine/eval_ragas.py` sets `QUESTIONS` to `lab0_millbrook/questions.json` while
`naive_rag.retrieve()` defaults to the *Fort Point* docs — Millbrook questions against a Boston
corpus. Fix the path first if you use RAGAS.

---

## 04 · Keep / patch / skip

| Path | | Why |
|------|---|-----|
| `Makefile` | KEEP | Add targets alongside; don't restructure |
| `lab0_boston/questions.json` | KEEP | Your eval set. Never edit it |
| `lab0_boston/DESIGN_NOTES.md` | KEEP | Answer key. Read, never index |
| `lab0_millbrook/naive_rag.py` | KEEP | This is your *baseline* — the "before" in every number. Build beside it |
| `lab0_millbrook/judge.py` | PATCH | Add `--pipeline` so it can score your system too |
| `boston/ingest.py` | PATCH | `--limit 2000` silently truncates every CSV |
| `boston/query.py` | PATCH | Good bones, right prompt. Becomes the retrieval branch of your router |
| `track_a_engine/hybrid_search.py` | KEEP | Actually works. Free points if hybrid is part of your story |
| `track_b_experience/app_streamlit.py` | KEEP | Your demo surface, whichever track |
| `track_a_engine/multi_source.py` | SKIP | TODO stub. Needs Docling + a PDF you don't have |
| `track_a_engine/eval_ragas.py` | SKIP | Broken path, heavy install, defaults to OpenAI |
| `lab0_millbrook/*` corpus | SKIP | Historical. Interesting tonight, irrelevant tomorrow |

---

## 05 · What you actually build

Four new files in one new package, plus two small patches. Nothing else changes, so the before/after
stays honest and the git diff tells the story.

```
rag-the-city-starter/
├── lab0_millbrook/naive_rag.py   # untouched: this is "before"
├── lab0_millbrook/judge.py       PATCH  --pipeline flag
├── boston/ingest.py              PATCH  --limit default, table registry
└── civic/                        NEW PACKAGE — all your work lives here
    ├── router.py       # classify: aggregate | temporal | lookup | unanswerable
    ├── tables.py       # CSV → DuckDB; count/date math happens here, in code
    ├── grounded.py     # evidence gate — abstain unless every claim is supported
    └── pipeline.py     # ask() — same signature as naive_rag.ask()
```

**The one design rule:** give `civic/pipeline.py` functions with the *identical signature* to
`naive_rag.retrieve()` and `naive_rag.generate()`. Then swapping baseline for yours is a one-line
import change — in the judge, in Streamlit, in your demo script.

- **router.py** — one small LLM call returning a label. "How many…", "how long…", "average…" go to
  code; everything else to retrieval. Log the label so the demo can show routing live. Highest-value file.
- **tables.py** — CSV-shaped docs + real 311 into DuckDB. `SELECT COUNT(*)` for counts, real date
  subtraction for durations. Return `(value, sql, rows)` so answers carry receipts.
- **grounded.py** — after drafting, a second call asks "is every claim present in the evidence?" If
  no, abstain. Kills 4B, probably 2B too.
- **pipeline.py** — router → branch → synthesize → gate. Under 150 lines.

### The judge patch, concretely

```python
ap.add_argument("--pipeline", default="lab0_millbrook.naive_rag")
mod = importlib.import_module(args.pipeline)
# then use mod.retrieve(...) / mod.generate(...) below
```

Now `make lab0-score` is your before, `--pipeline civic.pipeline` is your after — identical judge,
identical questions. That is what "measurably better than naive RAG" means to a judge, and almost
nobody in the room will have it.

---

## 06 · Test loop and traps

```bash
# single question, fastest signal — seconds
.venv/bin/python -m civic.pipeline "How many 311 requests list a location on the bridge?"

# full eval, both systems — minutes; run it maybe 4x all day
make lab0-score                                    # before: 21/24, 3 fabricated
.venv/bin/python -m lab0_millbrook.judge \
  --corpus-dir lab0_boston/corpus/docs \
  --collection fortpoint_naive \
  --questions lab0_boston/questions.json \
  --pipeline civic.pipeline                        # after: ?
```

**Four traps, an hour each if you meet them cold:**

1. **The index is cached and will not rebuild.** `build_index()` returns early on `if coll.count() > 0`.
   Change chunking and nothing happens — you're querying the old index. `rm -rf .chroma/lab0`, or
   better, use a new collection name per experiment so the baseline index stays intact for
   side-by-side runs.
2. **Two separate Chroma stores.** `.chroma/lab0` (Fort Point, `fortpoint_naive`) and `.chroma/boston`
   (real CSVs, `boston_open_data`). Wrong pair = empty or nonsense, no useful error.
3. **`ingest.py --limit 2000`.** Truncates every CSV to 2,000 rows by default. Every count over real
   311 data is wrong until you raise it or bypass the index for counting — which is what `tables.py` does.
4. **Ollama fails soft.** `generate()` catches everything and returns `None` to stderr. In a long
   scoring run this looks like bad answers, not a dead model. Check `ollama serve` before blaming the prompt.

### Tonight, 15 minutes

1. Read `DESIGN_NOTES.md` end to end — the only doc in the repo that tells you the truth.
2. Read `naive_rag.py`, all 137 lines. That's the whole architecture.
3. `make lab0-score | tee before.txt` — that file is the left half of your final slide.
4. Download the Operating Budget CSV plus one more dataset. Two minimum in the submission, and
   downloading is the part conference WiFi punishes.
