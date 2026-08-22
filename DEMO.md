# DEMO — read this off the screen

**The one line:** Retrieval fetches text. Counting is computation. We moved that line.

---

## 1. The failure

```
make baseline-ask-real Q="How many 311 service requests in the export were filed in Dorchester?"
```

Answers **2**. The truth is 9,974.

> "This is naive RAG on live Boston 311 data. Asked how many requests came from
> Dorchester, it says two. Look at what it retrieved — two parking complaints and
> a restaurant licence. Its index holds two thousand of seventy-eight thousand
> rows, so there was never a number it could retrieve that would be right."

---

## 2. The fix

```
make ask-real Q="How many 311 service requests in the export were filed in Dorchester?"
```

Prints `route: aggregate`, the SQL, then **9974**.

> "Same question. We classify it first. This one's an aggregate, so it goes to
> SQL over DuckDB, which reads the whole file — all seventy-eight thousand rows.
> Nine thousand nine hundred seventy-four. The query is the citation."

---

## 3. It can't drift

```
make prove
```

11/11 exact, under a second.

> "Eleven checks with no model in the loop at all. Five against the lab's
> hand-counted ground truth, six against live city data. These can't
> hallucinate, because nothing is guessing."

---

## 4. The numbers

```
.venv/bin/python -m eval.compare --before eval/results/before_real.txt --after eval/results/after_real.txt
```

> "Same judge, same ten questions, same two datasets. Fifty percent and four
> fabrications, to eighty percent and none. One regression we left on the board —
> A2 asks for two figures and our SQL path returns one."

---

## If they ask

**"How do you know 9,974 is right?"**
Three independent computations agree — pandas in the answer key, hand-written SQL
in the test, and model-written SQL at runtime that never sees the key.

**"Isn't capping at 2,000 rows unfair to the baseline?"**
Both sides use the same cap, it's the starter's default. And raising it doesn't
help — top-3 retrieval cannot produce a count of 9,974 at any k.

**"What about non-counting questions?"**
Retrieval, capped at 2,000 rows — same as the baseline. Our gain is on
computation and on knowing when to abstain.

**"What's your weakest point?"**
Multi-part questions. A2 and T1 both ask for two figures and one query returns
one. Known, stated in the README, not fixed.

---

## Datasets used (for the form)
- 311 Service Requests — 78,875 rows, Jan 1 – Aug 21 2026
- Food Establishment Inspections — 896,379 rows

**Track A — The Engine**
