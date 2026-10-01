#!/usr/bin/env python3
"""Download and validate legal open copies listed in missing-track indexes."""

from __future__ import annotations

import csv
import argparse
import html
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
INDEXES = (
    ROOT / "tracks/research/user-modeling-personalization-recommendation/index.tsv",
    ROOT / "tracks/research/web-mining-content-analysis/index.tsv",
    ROOT / "tracks/industry/index.tsv",
    ROOT / "tracks/short-papers/index.tsv",
    ROOT / "tracks/web4good/index.tsv",
)
MANIFEST = ROOT / "reports/download-manifest.tsv"
USER_AGENT = "Mozilla/5.0 (compatible; WWW26OpenCorpus/1.0; scholarly-download)"
SSL_CONTEXT = ssl.create_default_context()


def slugify(value: str, limit: int = 100) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return (value[:limit].rstrip("_") or "paper")


def fetch(url: str) -> tuple[bytes, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        },
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=90, context=SSL_CONTEXT) as response:
                return response.read(), response.headers.get_content_type(), response.geturl()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
            last_error = error
            if isinstance(error, urllib.error.HTTPError) and error.code in {401, 403, 404}:
                break
            time.sleep(3 * (attempt + 1))
        except Exception as error:
            last_error = error
            time.sleep(3 * (attempt + 1))
    assert last_error is not None
    raise last_error


def pdf_link_from_html(content: bytes, base_url: str) -> str | None:
    text = content.decode("utf-8", errors="ignore")
    patterns = (
        r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
        r'<link[^>]+type=["\']application/pdf["\'][^>]+href=["\']([^"\']+)',
        r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return urllib.parse.urljoin(base_url, html.unescape(match.group(1)))
    return None


def download(url: str) -> tuple[bytes, str]:
    content, content_type, final_url = fetch(url)
    if content.startswith(b"%PDF-"):
        return content, final_url
    if content_type in {"text/html", "application/xhtml+xml"}:
        candidate = pdf_link_from_html(content, final_url)
        if candidate and candidate != final_url:
            content, _, final_url = fetch(candidate)
            if content.startswith(b"%PDF-"):
                return content, final_url
    raise ValueError(f"not a PDF ({content_type}, {final_url})")


def valid_pdf(path: Path) -> int:
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("missing PDF signature")
    pages = len(PdfReader(path).pages)
    if pages < 1:
        raise ValueError("PDF has no pages")
    return pages


def save_manifest(rows: list[dict[str, str]]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    fields = ["paper_id", "track", "title", "doi", "source_url", "resolved_url", "pdf_file", "pages", "bytes", "status", "error"]
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry-failed", action="store_true", help="retry sources recorded as failed")
    args = parser.parse_args()
    previous: dict[str, dict[str, str]] = {}
    if MANIFEST.exists():
        with MANIFEST.open(encoding="utf-8", newline="") as stream:
            previous = {row["paper_id"]: row for row in csv.DictReader(stream, delimiter="\t")}

    manifest: list[dict[str, str]] = []
    candidates: list[tuple[Path, dict[str, str]]] = []
    for index in INDEXES:
        with index.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                if row.get("source_type") in {"open_pdf", "open_repository"}:
                    candidates.append((index.parent, row))

    for number, (track_dir, row) in enumerate(candidates, 1):
        pdf_dir = track_dir / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        destination = pdf_dir / f"{row['paper_id']}_{slugify(row['title'])}.pdf"
        item = {
            "paper_id": row["paper_id"],
            "track": row["track"],
            "title": row["title"],
            "doi": row["doi"],
            "source_url": row["open_url"],
            "resolved_url": "",
            "pdf_file": destination.relative_to(ROOT).as_posix(),
            "pages": "",
            "bytes": "",
            "status": "failed",
            "error": "",
        }
        old = previous.get(row["paper_id"])
        if (
            old
            and old.get("status") == "failed"
            and old.get("source_url") == row["open_url"]
            and not destination.exists()
            and not args.retry_failed
        ):
            manifest.append(old)
            save_manifest(manifest)
            print(f"[{number}/{len(candidates)}] SKIP known failure {row['paper_id']}")
            continue
        downloaded_now = False
        try:
            if destination.exists():
                pages = valid_pdf(destination)
                item.update(status="downloaded", pages=str(pages), bytes=str(destination.stat().st_size))
            else:
                content, resolved_url = download(row["open_url"])
                destination.write_bytes(content)
                downloaded_now = True
                pages = valid_pdf(destination)
                item.update(
                    status="downloaded",
                    resolved_url=resolved_url,
                    pages=str(pages),
                    bytes=str(len(content)),
                )
            print(f"[{number}/{len(candidates)}] OK {row['paper_id']} {item['pages']} pages")
        except Exception as error:  # keep the batch running and record exact failure
            if destination.exists():
                destination.unlink()
            item["error"] = f"{type(error).__name__}: {error}"
            printable_error = item["error"].encode("ascii", errors="backslashreplace").decode("ascii")
            print(f"[{number}/{len(candidates)}] FAIL {row['paper_id']} {printable_error}")
        manifest.append(item)
        save_manifest(manifest)
        if downloaded_now:
            time.sleep(0.5)

    success = sum(row["status"] == "downloaded" for row in manifest)
    print(f"downloaded and validated: {success}/{len(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
