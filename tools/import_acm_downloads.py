#!/usr/bin/env python3
"""Import browser-downloaded ACM PDFs and rebuild the complete download manifest."""

from __future__ import annotations

import csv
import html
import re
import shutil
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
MANIFEST = ROOT / "reports/download-manifest.tsv"
INDEXES = (
    ROOT / "tracks/research/user-modeling-personalization-recommendation/index.tsv",
    ROOT / "tracks/research/web-mining-content-analysis/index.tsv",
    ROOT / "tracks/industry/index.tsv",
    ROOT / "tracks/short-papers/index.tsv",
    ROOT / "tracks/web4good/index.tsv",
)
INDEX_FIELDS = ["paper_id", "track", "title", "doi", "doi_url", "open_url", "source_type", "code_url"]
MANIFEST_FIELDS = [
    "paper_id", "track", "title", "doi", "source_url", "resolved_url",
    "pdf_file", "pages", "bytes", "status", "error",
]


def slugify(value: str, limit: int = 100) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value[:limit].rstrip("_") or "paper"


def validate(path: Path) -> int:
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError(f"missing PDF signature: {path}")
    pages = len(PdfReader(path).pages)
    if pages < 1:
        raise ValueError(f"empty PDF: {path}")
    return pages


def main() -> int:
    previous: dict[str, dict[str, str]] = {}
    if MANIFEST.exists():
        with MANIFEST.open(encoding="utf-8", newline="") as stream:
            previous = {row["paper_id"]: row for row in csv.DictReader(stream, delimiter="\t")}

    manifest: list[dict[str, str]] = []
    imported = 0
    for index in INDEXES:
        with index.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        for row in rows:
            destination = index.parent / "pdf" / f"{row['paper_id']}_{slugify(row['title'])}.pdf"
            destination.parent.mkdir(parents=True, exist_ok=True)
            acm_source = DOWNLOADS / f"{row['doi'].removeprefix('10.1145/')}.pdf"
            source_url = row.get("open_url", "")
            resolved_url = ""

            if not destination.exists() and acm_source.exists():
                shutil.copy2(acm_source, destination)
                imported += 1
                source_url = f"https://dl.acm.org/doi/pdf/{row['doi']}?download=true"
                resolved_url = source_url
                row["open_url"] = source_url
                row["source_type"] = "official_pdf"

            pages = validate(destination)
            old = previous.get(row["paper_id"], {})
            if old.get("status") == "downloaded" and not resolved_url:
                source_url = old.get("source_url", source_url)
                resolved_url = old.get("resolved_url", "")
            manifest.append(
                {
                    "paper_id": row["paper_id"],
                    "track": row["track"],
                    "title": row["title"],
                    "doi": row["doi"],
                    "source_url": source_url,
                    "resolved_url": resolved_url,
                    "pdf_file": destination.relative_to(ROOT).as_posix(),
                    "pages": str(pages),
                    "bytes": str(destination.stat().st_size),
                    "status": "downloaded",
                    "error": "",
                }
            )

        with index.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, delimiter="\t", fieldnames=INDEX_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, delimiter="\t", fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(manifest)

    print(f"imported={imported} validated={len(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
