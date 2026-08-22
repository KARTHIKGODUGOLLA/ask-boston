"""Download the two Lab datasets from Analyze Boston via the CKAN API.

We resolve resource URLs at runtime with package_show instead of
hardcoding resource GUIDs — Analyze Boston rotates yearly CSV resources,
and a starter repo with a dead link on hack day helps nobody.

Targets (defaults for `make data`):
  * 311 Service Requests  — current-year CSV
  * Food Establishment Inspections

Run:  make data     (or: python boston/download.py)
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import requests

CKAN = "https://data.boston.gov/api/3/action/package_show"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "downloads"
DATASETS = ["311-service-requests", "food-establishment-inspections"]
YEAR = str(date.today().year)


def pick_csv(resources: list[dict]) -> dict | None:
    """Prefer a current-year CSV; fall back to the newest CSV resource."""
    csvs = [r for r in resources if (r.get("format") or "").upper() == "CSV" and r.get("url")]
    for r in csvs:
        if YEAR in (r.get("name") or "") or YEAR in r["url"]:
            return r
    return max(csvs, key=lambda r: r.get("last_modified") or r.get("created") or "", default=None)


def download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length") or 0)
        done = 0
        with dest.open("wb") as fh:
            for block in resp.iter_content(chunk_size=1 << 20):
                fh.write(block)
                done += len(block)
                mb = done / 1e6
                pct = f" ({100 * done // total}%)" if total else ""
                print(f"\r  {dest.name}: {mb:,.1f} MB{pct}", end="", flush=True)
    print()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0
    for slug in DATASETS:
        print(f"Resolving {slug} via CKAN package_show ...")
        try:
            resp = requests.get(CKAN, params={"id": slug}, timeout=30)
            resp.raise_for_status()
            resource = pick_csv(resp.json()["result"]["resources"])
            if resource is None:
                raise ValueError("no CSV resource found in package")
            dest = OUT_DIR / f"{slug}.csv"
            download(resource["url"], dest)
        except Exception as exc:
            failures += 1
            print(f"  [!] {slug} failed ({type(exc).__name__}): {exc}", file=sys.stderr)
            print(f"  [!] Grab it by hand: https://data.boston.gov/dataset/{slug}", file=sys.stderr)
    if failures:
        raise SystemExit(f"{failures} download(s) failed — are you online?")
    print(f"Done. CSVs are in {OUT_DIR} — next: python boston/ingest.py")


if __name__ == "__main__":
    main()
