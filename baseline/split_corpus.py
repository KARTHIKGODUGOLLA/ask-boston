"""Split a "## DOCUMENT N:" corpus into per-document files under a docs/ dir.

These corpora ship as ONE markdown file each. Real municipal data never
arrives that way, so we split on the "## DOCUMENT N:" headings to
simulate a multi-source corpus. naive_rag.py indexes the split files,
and inspecting a single failing doc is much easier than scrolling one
20+ KB wall of text.

Defaults are Lab 0 — The Fort Point Files: with no flags this splits
lab0_boston/corpus/fortpoint_full.md into eleven files under
lab0_boston/corpus/docs/. The original Millbrook corpus is reached via
explicit flags (the Makefile passes explicit flags for BOTH editions, so
behavior never depends on these defaults):

  python -m baseline.split_corpus \
      --input lab0_millbrook/corpus/millbrook_full.md \
      --outdir lab0_millbrook/corpus/docs

Millbrook output gets the attribution header below; any other corpus
keeps its own leading comment block (everything before the first
heading) as the per-file header — e.g. Fort Point's fiction disclaimer.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

MILLBROOK_CORPUS = Path(__file__).resolve().parent / "corpus"
MILLBROOK_FULL = MILLBROOK_CORPUS / "millbrook_full.md"
MILLBROOK_DOCS = MILLBROOK_CORPUS / "docs"

FORTPOINT_CORPUS = REPO_ROOT / "lab0_boston" / "corpus"
FORTPOINT_FULL = FORTPOINT_CORPUS / "fortpoint_full.md"
FORTPOINT_DOCS = FORTPOINT_CORPUS / "docs"

# Known corpora: expected heading counts (a changed corpus fails loudly)
# and the full-file each docs/ dir is generated from (used by naive_rag's
# auto-split).
EXPECTED_HEADINGS = {MILLBROOK_FULL: 10, FORTPOINT_FULL: 11}
FULL_FOR_DOCS = {MILLBROOK_DOCS: MILLBROOK_FULL, FORTPOINT_DOCS: FORTPOINT_FULL}

HEADING_RE = re.compile(r"^## DOCUMENT (\d+): (.+?)\s*$", re.M)

# Prepended to every generated Millbrook docs/ file. The splitter always
# regenerates docs/ from the full file (whose own header sits before the
# first heading and is never captured), so re-splitting stays idempotent.
ATTRIBUTION = """\
<!--
  Millbrook City RAG Challenge © William Caban — used with permission.
  All content is fictional, AI-generated synthetic data.
  Source: https://gist.github.com/williamcaban/8764f13aaa5c4b0768033671483f6c0f
  This corpus is NOT covered by this repository Apache-2.0 code license.
-->

"""


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def split(input_path: Path = FORTPOINT_FULL, outdir: Path = FORTPOINT_DOCS) -> list[Path]:
    input_path = Path(input_path).resolve()
    text = input_path.read_text(encoding="utf-8")
    matches = list(HEADING_RE.finditer(text))
    expected = EXPECTED_HEADINGS.get(input_path)
    if expected is not None and len(matches) != expected:
        raise SystemExit(
            f"Expected {expected} '## DOCUMENT N:' headings in {input_path.name}, "
            f"found {len(matches)} — corpus changed?"
        )
    if not matches:
        raise SystemExit(f"No '## DOCUMENT N:' headings found in {input_path}")
    if input_path == MILLBROOK_FULL:
        header = ATTRIBUTION
    else:  # carry the corpus's own preamble (e.g. its fiction disclaimer)
        preamble = text[:matches[0].start()].strip()
        header = preamble + "\n\n" if preamble else ""
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        num, title = int(m.group(1)), m.group(2)
        path = outdir / f"doc{num:02d}_{slugify(title)}.md"
        path.write_text(header + text[m.start():end].strip() + "\n", encoding="utf-8")
        written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a '## DOCUMENT N:' corpus into per-document files.")
    parser.add_argument("--input", type=Path, default=FORTPOINT_FULL,
                        help="corpus markdown file (default: Fort Point)")
    parser.add_argument("--outdir", type=Path, default=FORTPOINT_DOCS,
                        help="output directory (default: Fort Point corpus/docs)")
    args = parser.parse_args()
    for path in split(args.input, args.outdir):
        print(f"  {path.name}")
    print(f"Split {args.input.name} into {len(list(args.outdir.glob('doc*.md')))} documents -> {args.outdir}")


if __name__ == "__main__":
    main()
