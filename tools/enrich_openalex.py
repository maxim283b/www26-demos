#!/usr/bin/env python3
"""Find additional legal open copies for missing WWW'26 papers via OpenAlex."""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEXES = (
    ROOT / "tracks/research/user-modeling-personalization-recommendation/index.tsv",
    ROOT / "tracks/research/web-mining-content-analysis/index.tsv",
    ROOT / "tracks/industry/index.tsv",
    ROOT / "tracks/short-papers/index.tsv",
    ROOT / "tracks/web4good/index.tsv",
)


def query(dois: list[str]) -> list[dict]:
    values = "|".join(f"https://doi.org/{doi.lower()}" for doi in dois)
    params = urllib.parse.urlencode(
        {
            "filter": f"doi:{values}",
            "per-page": "100",
            "select": "doi,title,open_access,best_oa_location,locations",
        }
    )
    request = urllib.request.Request(
        f"https://api.openalex.org/works?{params}",
        headers={"User-Agent": "www26-proceedings-analysis/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["results"]


def candidate(work: dict) -> tuple[str, str] | None:
    locations = []
    if work.get("best_oa_location"):
        locations.append(work["best_oa_location"])
    locations.extend(work.get("locations") or [])
    for location in locations:
        url = location.get("pdf_url") or location.get("landing_page_url")
        if not url:
            continue
        host = urllib.parse.urlparse(url).hostname or ""
        if host not in {"doi.org", "dx.doi.org", "dl.acm.org", "www.scopus.com"}:
            return url, "open_pdf" if location.get("pdf_url") else "open_repository"
    return None


def main() -> int:
    rows_by_path: dict[Path, list[dict[str, str]]] = {}
    all_rows: list[dict[str, str]] = []
    for path in INDEXES:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        for row in rows:
            host = urllib.parse.urlparse(row.get("open_url", "")).hostname or ""
            if host in {"doi.org", "dx.doi.org"}:
                row["source_type"] = "publisher_page"
            elif host == "dl.acm.org":
                row["source_type"] = "publisher_pdf"
        rows_by_path[path] = rows
        all_rows.extend(rows)

    by_doi = {row["doi"].lower(): row for row in all_rows}
    found = 0
    for offset in range(0, len(all_rows), 25):
        batch = all_rows[offset : offset + 25]
        for work in query([row["doi"] for row in batch]):
            doi_url = work.get("doi") or ""
            doi = doi_url.removeprefix("https://doi.org/").lower()
            row = by_doi.get(doi)
            match = candidate(work)
            if row and match and row.get("source_type") not in {"open_pdf", "open_repository"}:
                row["open_url"], row["source_type"] = match
                found += 1
        print(f"checked {min(offset + len(batch), len(all_rows))}/{len(all_rows)}")
        time.sleep(1)

    fields = ["paper_id", "track", "title", "doi", "doi_url", "open_url", "source_type", "code_url"]
    for row in all_rows:
        row.setdefault("code_url", "")
    for path, rows in rows_by_path.items():
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, delimiter="\t", fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(f"new open copies found: {found}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
