# ask-boston

**RAG the City · The Open Accelerator, Boston · August 22, 2026 · Track A — The Engine**

| Who | Owns | Job |
|---|---|---|
| Karthik | `civic/router.py`, `civic/tables.py` | Routing + the compute path |
| TBD | `civic/grounded.py`, `app/` | Abstention + demo surface |
| TBD | `eval/` | Ground truth and the before/after numbers |

Naive RAG asked an 8B model to count 28 rows of a 311 export. It answered **10**.
The correct answer is **9**, and every one of those rows was sitting in the retrieved
context at the time.

That is not a retrieval problem and it is not a prompting problem. It is a category
error: retrieval fetches *text*, and the questions residents actually ask — *how many*,
*how long*, *is it getting worse* — are **computation**. ask-boston routes those
questions to code, keeps the language model for language, and refuses to answer at all
when the records don't support one.

---

## The thesis in one diagram

```
question
   |
router.route()                          deterministic regex first, model only on ties
   |
   +-- aggregate --> tables.answer()    text-to-SQL over DuckDB; the number is COMPUTED
   +-- temporal  --> temporal.compute() model reads dates, Python does the subtraction
   +-- lookup    --> retrieval.retrieve()  hybrid BM25 + dense (RRF), k=6, 60-word overlap
   |
synthesize (one call, evidence only)
   |
grounded.audit()  --+-- pass --> answer, with its SQL and sources attached
                    +-- fail --> "I don't know — the records don't say"
```

The audit is two checks, cheapest first: a free deterministic sweep for numbers that
appear in the answer but nowhere in the evidence, then one model call asking whether
every claim is supported. Fabrication is an automatic critical failure under the
rubric, so it gets a gate, not a prompt instruction.

## Prove it before you trust it

```bash
make setup      # venv + deps
make split      # regenerate the 11 Fort Point documents
make prove      # ← no model, under a second
```

`make prove` runs fixed SQL against the same rows the retriever would have handed the
model, and checks them against the hand-counted ground truth in
`lab0_boston/DESIGN_NOTES.md`:

```
  [PASS] Q9A  rows located on the bridge          expected 9, computed 9
  [PASS] Q9B  non-English submissions             expected 7, computed 7
  [PASS]      total rows in the export            expected 28, computed 28
  [PASS]      open cases                          expected 11, computed 11
  [PASS] Q3A  FY2027 design & engineering         expected 4200000, computed 4200000
```

No model was involved. These numbers cannot drift, hallucinate, or miscount.

## Measured against the baseline

The naive baseline is vendored **unmodified** at `baseline/`, and `eval/judge.py`
takes a `--pipeline` argument, so both systems face the identical grader, the
identical questions and the identical corpus.

Two suites, two jobs — see `eval/README.md`:

| suite | n | ground truth | proves |
|---|---|---|---|
| Fort Point | 24 | hand-counted in `DESIGN_NOTES.md`, with distractors | we beat naive RAG on a set that cannot move |
| Real 311 | 10 | computed in pandas, `verified_by` recorded per question | it works on the data we actually submit |

```bash
make score-before && make score-after            # Fort Point, 24 questions
make freeze-baseline && make ingest              # once, then freely
make score-before-real && make score-after-real  # real 311, 10 questions
make compare                                     # both, per question
```

### Two indexes, on purpose

`.chroma/baseline` is built once by `make freeze-baseline` and **never rebuilt**.
`boston/ingest.py` deletes and recreates its collection every run, so if the
control group shared that store, improving our chunking would improve the
baseline too — and since most of our gain comes from ingestion, we would be
handing our best work to the control group and measuring almost nothing.

**Fairness rule:** both sides index the same rows. `LIMIT` defaults to 2000 on
`make ingest` and `make freeze-baseline`. Change one, change the other.

Recorded baseline, `eval/results/before.txt`, 2026-08-22 11:23 —
**20.0/24 = 83% GOOD**, with fabrications on **2B and 9A**: a critical failure
under the rubric. Those two are the target, and both are the same defect:

| id | Category | Why it fails | What we do |
|----|----------|--------------|------------|
| 2B | Temporal Complexity | the duration is written in no document | extract the dates, subtract in Python |
| 9A | Aggregation & Counting | no chunk contains a count | `SELECT COUNT(*)` |
| 9B | Aggregation & Counting | scored only partial — the model counted by eye | same SQL path |

The baseline was asked to compute and it improvised. Two runs of the same judge
on the same corpus scored it 88% and 83% with different fabrications, which is
its own lesson: the band moves, the fabrications are the signal.

## Everything else

```bash
make data                                    # 311 + Food Inspections, CKAN-resolved
make tables                                  # what's registered in DuckDB right now
make ask Q="How many 311 requests list a location on the bridge?"
make baseline-ask Q="..."                    # the same question, naively — the contrast
make demo                                    # Streamlit, shows the route and the SQL
make clean-index                             # after changing chunking. It caches. It will bite you
```

## Layout

```
civic/          our work
  router.py       aggregate | temporal | lookup
  tables.py       CSV -> DuckDB, text-to-SQL, SELECT-only guard
  temporal.py     date extraction -> Python arithmetic
  retrieval.py    hybrid BM25 + dense, overlapping chunks, k=6
  grounded.py     numeric audit + claim audit -> abstention
  pipeline.py     orchestration; baseline-compatible retrieve()/generate()
  llm.py          one place that knows how to reach a model
eval/
  prove.py            no-LLM proof of the computed answers, both suites
  judge.py            the starter's judge, with --pipeline
  compare.py          before vs after
  questions_boston.json   10 real-data questions, ground truth verified in pandas
  README.md           how the measurement works, and how not to break it
baseline/       the control group — naive_rag.py (Fort Point), naive_boston.py
                (real CSVs), freeze.py. Do not fix these
boston/         Analyze Boston download / ingest / query
lab0_boston/    corpus, 24 eval questions, design notes — unmodified
app/            Streamlit demo surface
docs/           FIELD_MANUAL.md, DEMO_SCRIPT.md, SUBMISSION.md
```

## Datasets

From [Analyze Boston](https://data.boston.gov), resolved live through the CKAN API so
the links never rot:

1. **311 Service Requests** — 78,526 rows, Jan 1 – Aug 20 2026. The aggregation
   and multilingual surface. Ground truth in `eval/questions_boston.json` is pinned
   to this download; re-downloading invalidates it (`make prove` catches that)
2. **Food Establishment Inspections** — coded violations with no narrative cause, so
   "why?" questions are correctly unanswerable
3. **Operating Budget** — pairs with the narrative PDF; the contradiction case

## Running local

Defaults to `granite3.1-dense:8b` through Ollama, no cloud calls anywhere.
Set `CIVIC_SQL_MODEL=qwen2.5:7b` to route only text-to-SQL to a code-tuned model.

---

Derived from [rag-the-city-starter](https://github.com/holzerjm/rag-the-city-starter)
(Apache-2.0). See `NOTICE` for what was copied and what was changed. The Fort Point
corpus is fiction; see `lab0_boston/README.md`.
