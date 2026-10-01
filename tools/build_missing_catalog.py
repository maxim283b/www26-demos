#!/usr/bin/env python3
"""Build indexes for proceedings sections absent from the supplied PDF part."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium

from split_main_proceedings import toc_titles


@dataclass(frozen=True)
class Section:
    name: str
    folder: str
    first_doi: str


SECTIONS = (
    Section(
        "User Modeling, Personalization and Recommendation",
        "research/user-modeling-personalization-recommendation",
        "3774904.3792070",
    ),
    Section(
        "Web Mining and Content Analysis",
        "research/web-mining-content-analysis",
        "3774904.3792071",
    ),
    Section("Industry Track", "industry", "3774904.3792792"),
    Section("Short Papers", "short-papers", "3774904.3792845"),
    Section("Special Track: Web4Good", "web4good", "3774904.3793048"),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tracks",
    )
    args = parser.parse_args()

    document = pdfium.PdfDocument(args.source.resolve())
    titles = toc_titles(document)
    ordered_dois = list(titles)
    boundary_positions = [ordered_dois.index(section.first_doi) for section in SECTIONS]
    boundary_positions.append(len(ordered_dois))

    fields = ["paper_id", "track", "title", "doi", "doi_url", "open_url", "source_type", "code_url"]
    total = 0
    for index, section in enumerate(SECTIONS):
        rows = []
        for doi in ordered_dois[boundary_positions[index] : boundary_positions[index + 1]]:
            rows.append(
                {
                    "paper_id": "p" + doi.rsplit(".", 1)[-1],
                    "track": section.name,
                    "title": titles[doi],
                    "doi": f"10.1145/{doi}",
                    "doi_url": f"https://doi.org/10.1145/{doi}",
                    "open_url": "",
                    "source_type": "",
                    "code_url": "",
                }
            )

        destination = args.output.resolve() / section.folder / "index.tsv"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, delimiter="\t", fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        total += len(rows)
        print(f"{section.folder}: {len(rows)}")

    print(f"total: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
