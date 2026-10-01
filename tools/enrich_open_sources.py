#!/usr/bin/env python3
"""Add open full-text links from Semantic Scholar to missing-track indexes."""

from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEXES = (
    ROOT / "tracks/research/user-modeling-personalization-recommendation/index.tsv",
    ROOT / "tracks/research/web-mining-content-analysis/index.tsv",
    ROOT / "tracks/industry/index.tsv",
    ROOT / "tracks/short-papers/index.tsv",
    ROOT / "tracks/web4good/index.tsv",
)
API = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,externalIds,openAccessPdf,url"


def query(dois: list[str]) -> list[dict | None]:
    payload = json.dumps({"ids": [f"DOI:{doi}" for doi in dois]}).encode()
    request = urllib.request.Request(
        API,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "www26-proceedings-analysis/1.0"},
        method="POST",
    )
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 5:
                raise
            retry_after = int(error.headers.get("Retry-After", "30"))
            time.sleep(max(retry_after, 30) * (attempt + 1))
    raise RuntimeError("unreachable")


def main() -> int:
    rows_by_path: dict[Path, list[dict[str, str]]] = {}
    all_rows: list[dict[str, str]] = []
    for path in INDEXES:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        rows_by_path[path] = rows
        all_rows.extend(rows)

    found = 0
    for offset in range(0, len(all_rows), 100):
        batch = all_rows[offset : offset + 100]
        results = query([row["doi"] for row in batch])
        for row, result in zip(batch, results, strict=True):
            if not result:
                continue
            pdf = result.get("openAccessPdf") or {}
            url = pdf.get("url")
            if url:
                row["open_url"] = url
                host = urlparse(url).hostname or ""
                if host in {"doi.org", "dx.doi.org"}:
                    row["source_type"] = "publisher_page"
                elif host == "dl.acm.org":
                    row["source_type"] = "publisher_pdf"
                else:
                    row["source_type"] = "open_pdf"
                    found += 1
            elif result.get("url"):
                row["open_url"] = result["url"]
                row["source_type"] = "semantic_scholar_record"
        print(f"checked {min(offset + len(batch), len(all_rows))}/{len(all_rows)}")
        time.sleep(10)

    fields = ["paper_id", "track", "title", "doi", "doi_url", "open_url", "source_type", "code_url"]
    for row in all_rows:
        row.setdefault("code_url", "")
    for path, rows in rows_by_path.items():
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, delimiter="\t", fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(f"open PDFs found: {found}/{len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
