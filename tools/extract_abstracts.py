#!/usr/bin/env python3
"""Reconstruct OpenAlex abstracts and export a review-friendly TSV file."""

from __future__ import annotations

import csv
import json
from pathlib import Path


# OpenAlex had no abstract for these three records.  The concise fallback text
# is a paraphrase of the public bibliographic/institutional record, not a
# fabricated abstract; the provenance is exported alongside it.
FALLBACKS = {
    "des0925": (
        "MLPlatAgent turns a natural-language machine-learning task into a code-free visual "
        "workflow. It combines intent-based planning, hierarchical tool retrieval, and "
        "function-call workflow generation, and demonstrates the approach in two applied "
        "scenarios with preliminary comparisons against other LLM agents.",
        "EurekaMag bibliographic summary",
    ),
    "des1003": (
        "Swen is a cross-platform desktop assistant that lets a user select text in any "
        "application and invoke an LLM with a shortcut. It infers whether the user needs "
        "translation, explanation, or summarization and maintains a user profile to make "
        "later answers more personal and context-aware.",
        "EurekaMag bibliographic summary",
    ),
    "des1031": (
        "The system combines weak supervision over text, metadata, and image-derived signals "
        "with lightweight models and entity-graph inference. Its real-estate demo verifies "
        "new-development claims and exposes calibrated map scores, graph relations, and "
        "population overlays for interactive analyst inspection.",
        "Macquarie University publication record",
    ),
}


def restore_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    last = max(position for positions in inverted_index.values() for position in positions)
    words = [""] * (last + 1)
    for word, positions in inverted_index.items():
        for position in positions:
            words[position] = word
    return " ".join(words).strip()


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "tracks" / "demos"
    rows: list[dict[str, str]] = []
    for path in sorted((root / "metadata").glob("des*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        paper = payload.get("paper") or {}
        crossref = payload.get("crossref") or {}
        openalex = payload.get("openalex") or {}
        paper_id = paper.get("paper_id", path.stem)
        abstract = restore_abstract(openalex.get("abstract_inverted_index"))
        source = "OpenAlex abstract"
        if not abstract and paper_id in FALLBACKS:
            abstract, source = FALLBACKS[paper_id]
        rows.append(
            {
                "paper_id": paper_id,
                "title": paper.get("title", ""),
                "doi": crossref.get("DOI", ""),
                "abstract": abstract,
                "abstract_source": source,
                "topics": "; ".join(
                    topic.get("display_name", "") for topic in openalex.get("topics") or []
                ),
                "keywords": "; ".join(
                    item.get("display_name", "") for item in openalex.get("keywords") or []
                ),
            }
        )

    output = root / "abstracts.tsv"
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    covered = sum(bool(row["abstract"]) for row in rows)
    print(f"wrote {len(rows)} rows to {output}; abstracts available: {covered}/{len(rows)}")


if __name__ == "__main__":
    main()
