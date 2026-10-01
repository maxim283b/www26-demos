#!/usr/bin/env python3
"""Split the WWW'26 main-proceedings volume into per-paper PDFs.

The ACM volume contains article-level PDF bookmarks whose titles are DOI
suffixes.  Those bookmarks provide exact page boundaries and are more reliable
than detecting first pages from layout or OCR.  This script also reconstructs
titles from the printed table of contents and writes one TSV index per track.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium


DOI_RE = re.compile(r"3774904\.\d+")
TOC_ENTRY_RE = re.compile(
    r"[•�]\s*(.*?)\.{5,}\s*\d+\s*\n+"
    r"DOI:\s*https://doi\.org/10\.1145/(3774904\.\d+)",
    re.DOTALL,
)


@dataclass(frozen=True)
class Section:
    name: str
    folder: str
    first_doi: str


SECTIONS = (
    Section("Keynotes", "keynotes", "3774904.3787910"),
    Section(
        "Economics, Online Markets and Human Computation",
        "research/economics-online-markets-human-computation",
        "3774904.3792080",
    ),
    Section(
        "Graph Algorithms and Modeling for the Web",
        "research/graph-algorithms-modeling",
        "3774904.3792519",
    ),
    Section("Responsible Web", "research/responsible-web", "3774904.3792707"),
    Section(
        "Search and Retrieval-Augmented AI",
        "research/search-retrieval-augmented-ai",
        "3774904.3792665",
    ),
    Section("Security and Privacy", "research/security-privacy", "3774904.3792724"),
    Section("Semantics and Knowledge", "research/semantics-knowledge", "3774904.3792671"),
    Section(
        "Social Networks and Social Media",
        "research/social-networks-social-media",
        "3774904.3792704",
    ),
    Section(
        "Systems and Infrastructure for Web, Mobile, and Web of Things",
        "research/systems-infrastructure-web-mobile-iot",
        "3774904.3792697",
    ),
)


def slugify(value: str, limit: int = 110) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_text).strip("_")
    return slug[:limit].rstrip("_") or "paper"


def bookmark_rows(document: pdfium.PdfDocument) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for bookmark in document.get_toc():
        title = bookmark.get_title()
        destination = bookmark.get_dest()
        if DOI_RE.fullmatch(title) and destination:
            rows.append({"doi": title, "start": destination.get_index()})
    rows.sort(key=lambda row: int(row["start"]))
    for index, row in enumerate(rows):
        next_start = int(rows[index + 1]["start"]) if index + 1 < len(rows) else len(document)
        row["end"] = next_start - 1
    return rows


def toc_titles(document: pdfium.PdfDocument, last_page: int = 120) -> dict[str, str]:
    """Read the title immediately preceding each DOI line in the TOC.

    Walking backwards line-by-line also handles entries split across a page
    boundary, which a single multi-line regular expression can accidentally
    merge with the preceding authors.
    """
    titles: dict[str, str] = {}
    for index in range(min(last_page, len(document))):
        lines = [
            line.strip()
            for line in document[index]
            .get_textpage()
            .get_text_range()
            .replace("\r", "\n")
            .split("\n")
            if line.strip()
        ]
        for line_number, line in enumerate(lines):
            match = DOI_RE.search(line)
            if not match:
                continue
            parts: list[str] = []
            for candidate_index in range(line_number - 1, max(-1, line_number - 7), -1):
                candidate = lines[candidate_index]
                parts.append(candidate)
                if candidate.startswith(("•", "�")):
                    break
            title = " ".join(reversed(parts))
            title = re.sub(r"^[•�]\s*", "", title)
            title = re.sub(r"\.{2,}\s*\d+\s*$", "", title).strip()
            if title:
                titles[match.group(0)] = title
    return titles


def section_for(doi: str, ordered_dois: list[str]) -> Section:
    position = ordered_dois.index(doi)
    selected = SECTIONS[0]
    for section in SECTIONS:
        boundary = ordered_dois.index(section.first_doi)
        if position >= boundary:
            selected = section
        else:
            break
    return selected


def write_index(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "paper_id",
        "track",
        "title",
        "pages",
        "doi",
        "doi_url",
        "filename",
        "source_start_page",
        "source_end_page",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tracks",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    document = pdfium.PdfDocument(source)
    rows = bookmark_rows(document)
    if len(rows) != 504:
        raise RuntimeError(f"expected 504 article bookmarks, found {len(rows)}")

    titles = toc_titles(document)
    ordered_dois = [str(row["doi"]) for row in rows]
    by_folder: dict[str, list[dict[str, str]]] = {}

    for number, row in enumerate(rows, 1):
        doi = str(row["doi"])
        start = int(row["start"])
        end = int(row["end"])
        section = section_for(doi, ordered_dois)
        title = titles.get(doi, doi)
        paper_id = "p" + doi.rsplit(".", 1)[-1]
        filename = f"{paper_id}_{slugify(title)}.pdf"
        pdf_dir = output / section.folder / "pdf"
        destination = pdf_dir / filename
        pdf_dir.mkdir(parents=True, exist_ok=True)

        if args.force:
            for previous in pdf_dir.glob(f"{paper_id}_*.pdf"):
                if previous != destination:
                    previous.unlink()
        if args.force or not destination.exists():
            split = pdfium.PdfDocument.new()
            split.import_pages(document, pages=list(range(start, end + 1)))
            split.save(destination)
            split.close()

        metadata = {
            "paper_id": paper_id,
            "track": section.name,
            "title": title,
            "pages": str(end - start + 1),
            "doi": f"10.1145/{doi}",
            "doi_url": f"https://doi.org/10.1145/{doi}",
            "filename": filename,
            "source_start_page": str(start + 1),
            "source_end_page": str(end + 1),
        }
        by_folder.setdefault(section.folder, []).append(metadata)
        print(f"[{number:03d}/{len(rows)}] {section.folder}: {filename}")

    for folder, metadata_rows in by_folder.items():
        write_index(output / folder / "index.tsv", metadata_rows)

    print(f"split {len(rows)} papers from {source}")
    for folder, metadata_rows in by_folder.items():
        print(f"  {folder}: {len(metadata_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
