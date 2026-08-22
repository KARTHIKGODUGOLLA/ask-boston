# ask-boston

**RAG the City · The Open Accelerator, Boston · August 22, 2026 · Track A — The Engine**

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

The naive baseline is vendored **unmodified** at `baseline/naive_rag.py`, and
`eval/judge.py` takes a `--pipeline` argument, so both systems face the identical
grader, the identical 24 questions and the identical corpus.

```bash
make score-before      # baseline    -> eval/results/before.txt
make score-after       # ask-boston  -> eval/results/after.txt
make compare           # side by side, per question
```

Recorded baseline: **21.0/24 = 88% GOOD**, with fabrications on **2B, 4B, 9A** —
a critical failure under the rubric. Those three are the target:

| id | Category | Why it fails | What we do |
|----|----------|--------------|------------|
| 2B | Temporal Complexity | duration written in no document | extract dates, subtract in Python |
| 4B | Missing Context | the corpus deliberately omits the answer | evidence audit → abstain |
| 9A | Aggregation & Counting | no chunk contains a count | `SELECT COUNT(*)` |

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
  prove.py        no-LLM proof of the computed answers
  judge.py        the starter's judge, with --pipeline
  compare.py      before vs after
baseline/       the naive pipeline, unmodified — this is "before"
boston/         Analyze Boston download / ingest / query
lab0_boston/    corpus, 24 eval questions, design notes — unmodified
app/            Streamlit demo surface
docs/           FIELD_MANUAL.md, DEMO_SCRIPT.md, SUBMISSION.md
```

## Datasets

From [Analyze Boston](https://data.boston.gov), resolved live through the CKAN API so
the links never rot:

1. **311 Service Requests** — the aggregation and multilingual surface
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
