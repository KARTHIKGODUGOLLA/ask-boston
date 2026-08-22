"""before.txt vs after.txt, side by side. This is the final slide.

  make score-before && make score-after && make compare
"""
from __future__ import annotations

import re
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
ROW = re.compile(r"^\s*\[\s*\d+/\d+\]\s+(\S+)\s+(\S+)", re.M)
TOTAL = re.compile(r"^TOTAL: ([\d.]+) / (\d+)\s+->\s+(\d+)%\s+BAND: (.+)$", re.M)
FABS = re.compile(r"^FABRICATIONS: (.+?)(?:\s{2,}<--.*)?$", re.M)


def load(path: Path) -> tuple[dict[str, str], tuple[str, str, str], str]:
    if not path.exists():
        raise SystemExit(f"missing {path} — run `make score-before` and `make score-after` first")
    text = path.read_text(encoding="utf-8")
    verdicts = {qid: v for qid, v in ROW.findall(text)}
    t = TOTAL.search(text)
    total = (t.group(1), t.group(3), t.group(4)) if t else ("?", "?", "?")
    f = FABS.search(text)
    return verdicts, total, (f.group(1).strip() if f else "?")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--before", type=Path, default=RESULTS / "before.txt")
    ap.add_argument("--after", type=Path, default=RESULTS / "after.txt")
    args = ap.parse_args()

    before, btot, bfab = load(args.before)
    after, atot, afab = load(args.after)

    print(f"{args.before.stem} vs {args.after.stem}")
    print(f"{'id':<5}{'baseline':<20}{'ask-boston':<20}")
    print("-" * 45)
    changed = 0
    for qid in sorted(before.keys() | after.keys()):
        b, a = before.get(qid, "-"), after.get(qid, "-")
        mark = ""
        if b != a:
            changed += 1
            fixed = b in ("wrong", "fabricated") and a in ("correct", "partially_correct")
            mark = "  <-- fixed" if fixed else "  <-- REGRESSED"
        print(f"{qid:<5}{b:<20}{a:<20}{mark}")

    print("-" * 45)
    print(f"{'':<5}{btot[0] + ' pts':<20}{atot[0] + ' pts':<20}")
    print(f"{'':<5}{btot[1] + '%':<20}{atot[1] + '%':<20}")
    print(f"{'':<5}{btot[2]:<20}{atot[2]:<20}")
    print(f"\nfabrications   baseline: {bfab}\n               ask-boston: {afab}")
    print(f"verdicts changed: {changed}")


if __name__ == "__main__":
    main()
