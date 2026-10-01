#!/usr/bin/env python3
"""Search arXiv directly for WWW'26 papers whose DOI records lack open copies."""

from __future__ import annotations

import argparse
import csv
import difflib
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
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
ATOM = {"atom": "http://www.w3.org/2005/Atom"}


def normalized(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def score(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, normalized(left), normalized(right)).ratio()


def query(rows: list[dict[str, str]]) -> list[tuple[str, str]]:
    clauses = []
    for row in rows:
        title = re.sub(r"[\"\\]", " ", html.unescape(re.sub(r"<[^>]+>", " ", row["title"])))
        clauses.append(f'ti:"{title}"')
    params = urllib.parse.urlencode(
        {"search_query": " OR ".join(clauses), "start": "0", "max_results": str(len(rows) * 3)}
    )
    request = urllib.request.Request(
        f"https://export.arxiv.org/api/query?{params}",
        headers={"User-Agent": "www26-proceedings-analysis/1.0"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                root = ET.fromstring(response.read())
            result = []
            for entry in root.findall("atom:entry", ATOM):
                title = entry.findtext("atom:title", default="", namespaces=ATOM)
                identifier = entry.findtext("atom:id", default="", namespaces=ATOM).rstrip("/").rsplit("/", 1)[-1]
                identifier = identifier.removesuffix("v1").removesuffix("v2").removesuffix("v3").removesuffix("v4").removesuffix("v5")
                if title and identifier:
                    result.append((title, f"https://arxiv.org/pdf/{identifier}"))
            return result
        except (urllib.error.HTTPError, urllib.error.URLError, ET.ParseError) as error:
            if attempt == 4:
                print(f"SKIP batch after retries: {type(error).__name__}: {error}")
                return []
            time.sleep(10 * (attempt + 1))
    return []


def save(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, delimiter="\t", fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--failed-manifest",
        type=Path,
        help="limit the search to failed paper IDs from a download manifest",
    )
    args = parser.parse_args()
    failed_ids: set[str] | None = None
    if args.failed_manifest:
        with args.failed_manifest.open(encoding="utf-8", newline="") as stream:
            failed_ids = {
                row["paper_id"]
                for row in csv.DictReader(stream, delimiter="\t")
                if row.get("status") == "failed"
            }

    rows_by_path: dict[Path, list[dict[str, str]]] = {}
    unresolved: list[dict[str, str]] = []
    for path in INDEXES:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        for row in rows:
            row.setdefault("code_url", "")
            if failed_ids is not None:
                if row["paper_id"] in failed_ids:
                    unresolved.append(row)
            elif row.get("source_type") not in {"open_pdf", "open_repository"}:
                unresolved.append(row)
        rows_by_path[path] = rows

    found = 0
    for offset in range(0, len(unresolved), 8):
        batch = unresolved[offset : offset + 8]
        results = query(batch)
        used: set[str] = set()
        for row in batch:
            matches = sorted(
                ((score(row["title"], title), url) for title, url in results if url not in used),
                reverse=True,
            )
            if matches and matches[0][0] >= 0.86:
                row["open_url"] = matches[0][1]
                row["source_type"] = "open_pdf"
                used.add(matches[0][1])
                found += 1
                print(f"FOUND {row['paper_id']} {matches[0][0]:.3f} {matches[0][1]}")
        for path, rows in rows_by_path.items():
            save(path, rows)
        print(f"checked {min(offset + len(batch), len(unresolved))}/{len(unresolved)}, found {found}")
        time.sleep(3)

    print(f"arXiv title search found: {found}/{len(unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
