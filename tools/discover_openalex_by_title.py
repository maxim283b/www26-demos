#!/usr/bin/env python3
"""Find unmerged preprint records by exact paper title in OpenAlex."""

from __future__ import annotations

import csv
import difflib
import html
import json
import re
import time
import urllib.error
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
FIELDS = ["paper_id", "track", "title", "doi", "doi_url", "open_url", "source_type", "code_url"]
BLOCKED_HOSTS = {"doi.org", "dx.doi.org", "dl.acm.org", "www.scopus.com", "link.springer.com"}


def normalized(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def score(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, normalized(left), normalized(right)).ratio()


def query(title: str) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "search": title,
            "per-page": "5",
            "select": "doi,title,open_access,best_oa_location,locations",
        }
    )
    request = urllib.request.Request(
        f"https://api.openalex.org/works?{params}",
        headers={"User-Agent": "www26-proceedings-analysis/1.0"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)["results"]
        except urllib.error.HTTPError as error:
            if error.code == 400:
                print(f"SKIP HTTP 400: {title}")
                return []
            if error.code != 429:
                raise
            if attempt == 4:
                print(f"SKIP HTTP 429 after retries: {title}")
                return []
            time.sleep(10 * (attempt + 1))
    return []


def candidate(work: dict) -> tuple[str, str] | None:
    locations = []
    if work.get("best_oa_location"):
        locations.append(work["best_oa_location"])
    locations.extend(work.get("locations") or [])
    seen: set[str] = set()
    for location in locations:
        url = location.get("pdf_url") or location.get("landing_page_url")
        if not url or url in seen:
            continue
        seen.add(url)
        host = urllib.parse.urlparse(url).hostname or ""
        if host not in BLOCKED_HOSTS:
            kind = "open_pdf" if location.get("pdf_url") else "open_repository"
            return url, kind
    return None


def save(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, delimiter="\t", fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rows_by_path: dict[Path, list[dict[str, str]]] = {}
    unresolved: list[dict[str, str]] = []
    for path in INDEXES:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        for row in rows:
            row.setdefault("code_url", "")
            if row.get("source_type") not in {"open_pdf", "open_repository"}:
                unresolved.append(row)
        rows_by_path[path] = rows

    found = 0
    for number, row in enumerate(unresolved, 1):
        best: tuple[float, dict] | None = None
        for work in query(row["title"]):
            similarity = score(row["title"], work.get("title") or "")
            if similarity >= 0.90 and (best is None or similarity > best[0]):
                best = similarity, work
        if best:
            match = candidate(best[1])
            if match:
                row["open_url"], row["source_type"] = match
                found += 1
                print(f"FOUND {row['paper_id']} {match[0]}")
                for path, rows in rows_by_path.items():
                    save(path, rows)
        if number % 25 == 0:
            for path, rows in rows_by_path.items():
                save(path, rows)
            print(f"checked {number}/{len(unresolved)}, found {found}")
        time.sleep(1.2)

    for path, rows in rows_by_path.items():
        save(path, rows)
    print(f"title search found: {found}/{len(unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
