# eval/ — where our score comes from

Two suites, two jobs. Run both; lead with the first.

| suite | file | n | ground truth | what it proves |
|---|---|---|---|---|
| **Fort Point** | `../lab0_boston/questions.json` | 24 | hand-counted in `DESIGN_NOTES.md`, with pre-written distractors | that we beat naive RAG, measurably, on a calibrated set that does not move |
| **Real data** | `questions_boston.json` | 10 | computed in pandas over the actual 311 export; each entry carries its `verified_by` expression | that it works on the datasets we actually submit |

Fort Point is the headline. It is fiction, but it is the only set where the
answers are *fixed* — the corpus cannot change under us, the distractors were
written by people who knew exactly how a RAG fails, and we already have the
baseline's number on it. That makes it the honest before/after.

The real-data suite is the credibility. A judge who watches us win on invented
documents will ask whether it works on Boston. This answers that.

```bash
make score-before        # Fort Point, naive baseline
make score-after         # Fort Point, ours
make score-before-real   # real 311, frozen baseline
make score-after-real    # real 311, ours
make compare             # both, side by side, per question
```

## Question schema

```json
{
  "id": "A1",
  "category": "Aggregation & Counting",
  "difficulty": "Easy",
  "question": "...",
  "expected_answer": "...",
  "wrong_answers": ["the specific wrong answers a RAG is likely to give"],
  "verified_by": "the pandas expression that produced the ground truth"
}
```

`wrong_answers` is the part that matters. The judge sees them as named
distractors, which is what makes it catch a confident near-miss instead of
waving it through.

## Adding questions — answer key first

Write the answer key first, computed from the CSVs, then write the question to
match. Never write a question whose answer you have not verified in pandas: an
eval set with guessed ground truth scores noise.

## The real-data ground truth is pinned to one download

The 10 seeded questions were verified against a specific
`data/downloads/311-service-requests.csv` — **78,526 rows, Jan 1 – Aug 20 2026.**
`make data` re-resolves the current CSV through CKAN, so a re-download tomorrow
returns a *larger* file and every count in `questions_boston.json` goes stale.

`make prove` catches this: if the Fort Point cases pass and only the real-data
cases fail, the CSV grew. **Re-verify the counts in pandas and update the
question file — never "fix" the SQL to match.**

If you change or add a dataset: re-download, re-verify the ground truth,
`make freeze-baseline --force`, `make ingest`. In that order.

## Two indexes, on purpose

| index | built by | read by | rebuild? |
|---|---|---|---|
| `.chroma/baseline` | `make freeze-baseline` | the naive control group | **never** |
| `.chroma/boston` | `make ingest` | our pipeline, real data | freely |
| `.chroma/civic` | first query | our pipeline, Fort Point | freely |

They are separate because `boston/ingest.py` deletes and recreates its
collection on every run. If the control group shared that index, then the
moment we improved chunking the baseline would improve too — and since most of
our gain comes from ingestion, we would be handing our best work to the control
group and measuring almost nothing.

`baseline/naive_rag.py` and `baseline/naive_boston.py` are the **control group.
Do not fix them, do not re-freeze them.** Every point we score is the gap
between them and us, so they have to stay broken.

**Fairness rule:** both sides must index the same rows. `LIMIT` defaults to
2000 for `make ingest` and `make freeze-baseline`. Change one, change the other,
or the comparison is worthless and a judge will say so.

## Scoring

`correct = 1.0` · `partially_correct = 0.5` · `wrong = 0` · **`fabricated = 0` and flagged**

Fabrication is called out separately because the rubric makes a confident lie a
CRITICAL FAILURE — worse than a miss. Getting fabrications to zero is worth more
than raising the percentage.

**The judge is lenient and it drifts.** It is Granite grading Granite, and the
same run twice can differ by a point. Save every run to a file with its
timestamp (`--save` does this). A saved file is evidence; a remembered number
is a claim.
