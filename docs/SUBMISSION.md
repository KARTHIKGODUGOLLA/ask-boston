# Submission checklist — due 3:15 PM sharp

Code freeze is 3:15. Round 1 demos start at 3:30. After 3:15 you rehearse, you do not debug.

## The four required items

- [ ] **Public repo link** — GitHub/GitLab, public, working code
      `_______________________________________________`
- [ ] **2-minute demo video, recorded** — not live. Record it by 2:45
      `_______________________________________________`
- [ ] **Declared track** — A (Engine). Locked at 10:45, no switching
- [ ] **Datasets used, minimum two, from Analyze Boston**
      1. 311 Service Requests
      2. Food Establishment Inspections
      3. Operating Budget (if the contradiction case makes the cut)

## Timeline

| time | do this |
|------|---------|
| 9:30 | doors. `make setup`, `make data`, `make prove` — confirm green on every laptop |
| 10:30 | matchmaking if you still need people |
| 10:45 | **track locks.** `make score-before` — saves to eval/results/before.txt. This number is your left column |
| 10:50 | `make freeze-baseline` ONCE, then `make ingest`. Same LIMIT on both, or the comparison is worthless |
| 11:00 | build. router first, then tables, then the gate |
| 13:30 | first full `make score-after`. Whatever it says, you now have a real result |
| 14:15 | last code change worth making. Then `make score-after` again and `make compare` |
| 14:45 | **record the video.** Not at 3:10 |
| 15:00 | push, make the repo public, paste the links into the form |
| 15:15 | freeze |

## Before you push

- [ ] `.venv/`, `.chroma/`, `data/downloads/` are gitignored — they are, but check
- [ ] `eval/results/before.txt` and `after.txt` are committed. The numbers are the argument
- [ ] `make prove` passes on a fresh clone
- [ ] README's baseline numbers match what actually ran today
- [ ] `NOTICE` is intact — the starter is Apache-2.0 and the corpus is someone's work
- [ ] `make prove` still passes on the REAL data. If only those cases fail, the
      311 CSV grew since the ground truth was verified — re-verify in pandas and
      update `eval/questions_boston.json`. Never edit the SQL to match

## Guard rails

**Do not edit `lab0_boston/questions.json`.** Editing the test is the one thing that
turns a good result into a disqualified one.

**Do not touch `baseline/naive_rag.py`.** It is the "before" in every number you show.

**Record the before-number in a file, with a timestamp.** The judge drifts a point or
two between runs. A saved file is evidence; a remembered number is a claim.
