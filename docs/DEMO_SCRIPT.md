# The two-minute demo

Record it, don't perform it live. Screen capture with narration, one take per section,
stitched. Budget: 15 minutes to record, 15 to cut, done by 2:45.

## The shape

**0:00–0:15 · The failure, not the premise**

Terminal, split or sequential:

```
make baseline-ask Q="How many 311 requests list a location on the Northern Avenue Bridge?"
```

It answers **10**, and helpfully lists ten items. Let that sit for a beat.

> "Naive RAG was handed all 28 rows and asked to count. It said ten. The answer is nine.
> Every row it needed was already in its context — so this was never a retrieval problem."

**0:15–0:35 · The same question, ours**

```
make ask Q="How many 311 requests list a location on the Northern Avenue Bridge?"
```

The route line prints `aggregate`, the SQL prints, the answer is **9**.

> "We classify the question first. Counting goes to SQL over DuckDB, not to the model.
> The number is computed, and the query that computed it is the citation."

**0:35–0:55 · It can't drift**

```
make prove
```

Five PASS lines against the hand-counted ground truth, in under a second, with no model
running.

> "No model in this loop. These numbers can't hallucinate or miscount."

**0:55–1:20 · Knowing when to stop**

```
make ask Q="What caused Gull & Anchor Bakery's walk-in cooler failure?"
```

The gate fires; the answer is the abstention.

> "The inspection report has violation codes and no cause. The baseline invents a
> compressor failure. We audit every answer against its evidence before showing it —
> a number that isn't in the evidence blocks the answer outright. Fabrication is an
> automatic critical failure under the rubric, so we made it structurally impossible
> rather than asking the prompt nicely."

**1:20–1:50 · The numbers**

```
make compare
```

Per-question, baseline vs ours, then the totals and the fabrication lines.

> "Same judge, same 24 questions, same corpus — the baseline is vendored unmodified
> and the grader takes a --pipeline flag. Baseline: 88%, three fabrications, which
> the rubric calls a critical failure. Ours: [N]%, [N] fabrications."

**1:50–2:00 · Close**

> "Retrieval fetches text. Counting is computation. Every civic question a resident
> actually asks — how many, how long, is it getting worse — is on the wrong side of
> that line for naive RAG, and that's the line we moved."

## Rules

- **Never run `make score-after` live on camera.** Two minutes of a progress bar.
  Show the saved `compare` output.
- **Pre-warm every index** before recording. First query rebuilds Chroma and takes
  30 seconds you don't have.
- **Bump your terminal font to ~18pt.** It's a projector.
- **Say a number in the first fifteen seconds.** 10 vs 9 is the whole pitch, and it
  fits in one breath.
- If a demo command is slow, record it, then cut the dead air. Nobody is checking
  wall-clock honesty on a screen capture; they are checking whether you can explain
  what your system does.
