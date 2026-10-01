#!/usr/bin/env python3
"""Build a bookmarked PDF collection from the validated open-paper manifest."""

from __future__ import annotations

import csv
import html
import logging
import textwrap
from collections import OrderedDict
from datetime import date
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

logging.getLogger("pypdf").setLevel(logging.ERROR)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/download-manifest.tsv"
OUTPUT = ROOT / "output/pdf/www26-open-papers-collection.pdf"
FRONTMATTER = ROOT / "tmp/pdfs/www26-open-papers-frontmatter.pdf"
REPORT = ROOT / "reports/collection-manifest.md"
WIDTH, HEIGHT = A4
MARGIN = 42
BOTTOM = 42
ACCENT = HexColor("#1570EF")
INK = HexColor("#172B4D")
MUTED = HexColor("#5E6C84")


def clean(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("<sup>", "^").replace("</sup>", "")
    return " ".join(value.split())


def wrapped(text: str, width: float, font: str, size: float) -> list[str]:
    words = clean(text).split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = word if not line else f"{line} {word}"
        if stringWidth(trial, font, size) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines or [""]


def load_rows() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        rows = [row for row in csv.DictReader(stream, delimiter="\t") if row["status"] == "downloaded"]
    for row in rows:
        path = ROOT / row["pdf_file"]
        if not path.exists():
            raise FileNotFoundError(path)
        actual_pages = len(PdfReader(path).pages)
        if actual_pages != int(row["pages"]):
            raise ValueError(f"page-count mismatch for {path}: {actual_pages} != {row['pages']}")
    return rows


def plan_toc(rows: list[dict[str, str]]) -> list[list[tuple[str, dict[str, str] | str]]]:
    pages: list[list[tuple[str, dict[str, str] | str]]] = []
    page: list[tuple[str, dict[str, str] | str]] = []
    remaining = HEIGHT - 92 - BOTTOM
    last_track = ""
    for row in rows:
        if row["track"] != last_track:
            required = 23
            if remaining < required + 30:
                pages.append(page)
                page = []
                remaining = HEIGHT - 92 - BOTTOM
            page.append(("track", row["track"]))
            remaining -= required
            last_track = row["track"]
        title_lines = wrapped(row["title"], WIDTH - 2 * MARGIN - 24, "Helvetica", 7.2)
        required = 8.6 * len(title_lines) + 9.5
        if remaining < required:
            pages.append(page)
            page = [("track-cont", f"{row['track']} (continued)")]
            remaining = HEIGHT - 92 - BOTTOM - 23
        page.append(("paper", row))
        remaining -= required
    if page:
        pages.append(page)
    return pages


def draw_header(c: canvas.Canvas, title: str, page_no: int | None = None) -> None:
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(MARGIN, HEIGHT - 52, title)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(2)
    c.line(MARGIN, HEIGHT - 62, WIDTH - MARGIN, HEIGHT - 62)
    if page_no is not None:
        c.setFont("Helvetica", 8)
        c.setFillColor(MUTED)
        c.drawRightString(WIDTH - MARGIN, 24, str(page_no))


def make_frontmatter(rows: list[dict[str, str]], toc_pages: list[list[tuple[str, dict[str, str] | str]]]) -> int:
    FRONTMATTER.parent.mkdir(parents=True, exist_ok=True)
    total_source_pages = sum(int(row["pages"]) for row in rows)
    front_count = 1 + len(toc_pages)
    cumulative = 0
    starts: dict[str, int] = {}
    for row in rows:
        starts[row["paper_id"]] = front_count + cumulative + 1
        cumulative += int(row["pages"])

    c = canvas.Canvas(str(FRONTMATTER), pagesize=A4, pageCompression=1)
    c.setTitle("The Web Conference 2026 — Open Papers Collection")
    c.setAuthor("www27-demos research corpus")
    c.setFillColor(ACCENT)
    c.rect(0, HEIGHT - 14, WIDTH, 14, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(MARGIN, HEIGHT - 105, "The Web Conference 2026")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(MARGIN, HEIGHT - 139, "Open Papers Collection")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 11)
    c.drawString(MARGIN, HEIGHT - 176, "Research tracks 9–10, Industry, Short Papers, and Web4Good")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 44)
    c.drawString(MARGIN, HEIGHT - 260, str(len(rows)))
    c.setFont("Helvetica", 12)
    c.drawString(MARGIN + 92, HEIGHT - 248, "validated open papers")
    c.drawString(MARGIN + 92, HEIGHT - 268, f"{total_source_pages:,} article pages")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    note = (
        "This research corpus contains publicly accessible ACM copies, author manuscripts, preprints, "
        "and repository copies. The authoritative publication record is identified by the ACM DOI."
    )
    y = HEIGHT - 340
    for line in wrapped(note, WIDTH - 2 * MARGIN, "Helvetica", 9):
        c.drawString(MARGIN, y, line)
        y -= 13
    c.drawString(MARGIN, 42, f"Generated {date.today().isoformat()} · ordered by proceedings track")
    c.showPage()

    for index, entries in enumerate(toc_pages, 1):
        draw_header(c, "Contents", index + 1)
        y = HEIGHT - 84
        for kind, payload in entries:
            if kind.startswith("track"):
                c.setFillColor(ACCENT)
                c.setFont("Helvetica-Bold", 9.2)
                c.drawString(MARGIN, y, clean(str(payload)))
                y -= 15
                continue
            row = payload
            assert isinstance(row, dict)
            c.setFillColor(INK)
            c.setFont("Helvetica", 7.2)
            title_lines = wrapped(row["title"], WIDTH - 2 * MARGIN - 31, "Helvetica", 7.2)
            for line_no, line in enumerate(title_lines):
                prefix = f"{row['paper_id'][1:]}  " if line_no == 0 else " " * 10
                c.drawString(MARGIN + 7, y, prefix + line)
                y -= 8.6
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 6.5)
            c.drawString(MARGIN + 31, y, f"doi:{row['doi']}  ·  collection page {starts[row['paper_id']]}")
            y -= 9.5
        c.showPage()
    c.save()
    return front_count


def build(rows: list[dict[str, str]], front_count: int) -> tuple[int, int]:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.append(str(FRONTMATTER), import_outline=False)
    current_page = front_count
    parents: dict[str, object] = {}
    for number, row in enumerate(rows, 1):
        source = ROOT / row["pdf_file"]
        if row["track"] not in parents:
            parents[row["track"]] = writer.add_outline_item(clean(row["track"]), current_page)
        writer.add_outline_item(
            f"{row['paper_id']} — {clean(row['title'])}",
            current_page,
            parent=parents[row["track"]],
        )
        writer.append(str(source), import_outline=False)
        current_page += int(row["pages"])
        if number % 25 == 0:
            print(f"appended {number}/{len(rows)} papers", flush=True)
    writer.add_metadata(
        {
            "/Title": "The Web Conference 2026 — Open Papers Collection",
            "/Author": "www27-demos research corpus",
            "/Subject": "Publicly accessible copies from missing WWW 2026 proceedings tracks",
            "/Keywords": "WWW 2026, The Web Conference, open access, research corpus",
        }
    )
    writer.page_mode = "/UseOutlines"
    with OUTPUT.open("wb") as stream:
        writer.write(stream)
    return current_page, OUTPUT.stat().st_size


def write_report(rows: list[dict[str, str]], pages: int, size: int, front_count: int) -> None:
    groups: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        groups.setdefault(row["track"], []).append(row)
    lines = [
        "# Open papers collection",
        "",
        f"- Papers: **{len(rows)}**",
        f"- Article pages: **{sum(int(row['pages']) for row in rows):,}**",
        f"- Front matter pages: **{front_count}**",
        f"- Total collection pages: **{pages:,}**",
        f"- File size: **{size / 1024 / 1024:.1f} MiB**",
        "- Source inventory: `reports/download-manifest.tsv`",
        "",
        "## Tracks",
        "",
        "| Track | Papers | Article pages |",
        "|---|---:|---:|",
    ]
    for track, items in groups.items():
        lines.append(f"| {clean(track)} | {len(items)} | {sum(int(row['pages']) for row in items):,} |")
    lines += [
        "",
        "The collection includes only files that passed PDF signature and page-count validation. "
        "For publication metadata and source URLs, see the track indexes and coverage report.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = load_rows()
    toc_pages = plan_toc(rows)
    front_count = make_frontmatter(rows, toc_pages)
    pages, size = build(rows, front_count)
    write_report(rows, pages, size, front_count)
    print(f"built {OUTPUT} ({pages} pages, {size / 1024 / 1024:.1f} MiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
