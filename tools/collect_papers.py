#!/usr/bin/env python3
"""Build the WebConf'26 demo corpus index and download open PDF copies.

The official accepted-papers page is the source of truth for membership in the
corpus. Crossref supplies DOI/page metadata. OpenAlex, Unpaywall, Semantic
Scholar, and arXiv are queried only to locate legal open-access PDF copies.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ACCEPTED_URL = "https://www2026.thewebconf.org/accepted/demo.html"
CROSSREF_API = "https://api.crossref.org/works"
USER_AGENT = "webconf-demo-corpus/1.0 (research corpus builder)"

# Exact author/institutional copies found outside the metadata APIs.  Keeping
# them in code makes the corpus reproducible instead of relying on files that
# happened to be downloaded during an exploratory run.
MANUAL_PDF_URLS = {
    "des0206": "https://cdn.amazon.science/74/3e/4a1b196b4c639e4106de4bbb7333/scipub-approval152129-42965177-pattern-discovery-with-widelens-analysis-and-sharpfocus-validation.pdf",
    "des0502": "https://research.deepractice.ai/2026_WWW_Demo.pdf",
    "des0949": "https://arxiv.org/pdf/2601.12260",
    "des0953": "https://upcommons.upc.edu/server/api/core/bitstreams/68a7f84c-62c5-43a4-9552-bbf86415a7ab/content",
    "des987": "https://raw.githubusercontent.com/ai4society/ai4society.github.io/main/publications/papers_local/ARC_Demo_WebConference2026.pdf",
    "des1017": "https://repositum.tuwien.at/bitstream/20.500.12708/230838/1/Guenes-2026-MetriKG%20Profiling%20Static%20and%20Evolving%20Knowledge%20Graphs-vor.pdf",
    "des1031": "https://researchers.mq.edu.au/files-asset/539535862/538929497.pdf/",
}


def request(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None,
            attempts: int = 3) -> bytes:
    merged = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        merged.update(headers)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, data=data, headers=merged)
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - transient public APIs are retried
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 2)
    assert last_error is not None
    raise last_error


def get_json(url: str) -> dict:
    return json.loads(request(url, headers={"Accept": "application/json"}))


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip(" \n\r\t—")


def normalize_title(value: str) -> str:
    value = html.unescape(value).lower()
    value = value.replace("‑", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def title_score(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def slugify(value: str, limit: int = 96) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value[:limit].rstrip("_") or "paper"


def parse_accepted(raw_html: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r'<li>\s*<span class="paper-id">\((des\d+)\)</span>(.*?)—\s*'
        r'<span class="paper-authors"[^>]*>(.*?)</span',
        re.DOTALL | re.IGNORECASE,
    )
    papers = []
    for paper_id, raw_title, raw_authors in pattern.findall(raw_html):
        papers.append({
            "paper_id": paper_id,
            "title": clean_text(raw_title),
            "authors": clean_text(raw_authors),
        })
    if len(papers) < 35:
        raise RuntimeError(f"accepted-page parser found only {len(papers)} papers")
    return papers


def crossref_lookup(title: str) -> dict:
    params = {
        "query.title": title,
        "filter": "from-pub-date:2026-01-01,until-pub-date:2026-12-31",
        "select": "DOI,title,page,link,container-title,URL,author",
        "rows": "5",
    }
    payload = get_json(f"{CROSSREF_API}?{urllib.parse.urlencode(params)}")
    candidates = payload.get("message", {}).get("items", [])
    ranked = []
    for item in candidates:
        candidate_title = (item.get("title") or [""])[0]
        score = title_score(title, candidate_title)
        container = " ".join(item.get("container-title") or [])
        if "Companion Proceedings of the ACM Web Conference 2026" in container:
            score += 0.25
        ranked.append((score, item))
    if not ranked:
        return {}
    score, item = max(ranked, key=lambda pair: pair[0])
    return item if score >= 0.86 else {}


def openalex_lookup(doi: str) -> dict:
    if not doi:
        return {}
    url = "https://api.openalex.org/works/" + urllib.parse.quote(f"https://doi.org/{doi}", safe="")
    try:
        return get_json(url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return {}


def unpaywall_lookup(doi: str) -> dict:
    if not doi:
        return {}
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email=research@example.com"
    try:
        return get_json(url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return {}


def semantic_scholar_lookup(title: str) -> dict:
    params = {"query": title, "limit": "5", "fields": "title,externalIds,openAccessPdf,url"}
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    try:
        payload = get_json(url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return {}
    ranked = [
        (title_score(title, item.get("title", "")), item)
        for item in payload.get("data", [])
    ]
    if not ranked:
        return {}
    score, item = max(ranked, key=lambda pair: pair[0])
    return item if score >= 0.92 else {}


def arxiv_lookup(title: str) -> dict:
    query = f'ti:"{title}"'
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": query,
        "start": "0",
        "max_results": "5",
    })
    try:
        root = ET.fromstring(request(url, headers={"Accept": "application/atom+xml"}))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ET.ParseError):
        return {}
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    ranked = []
    for entry in root.findall("atom:entry", ns):
        found_title = " ".join((entry.findtext("atom:title", default="", namespaces=ns)).split())
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("type") == "application/pdf" or link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href", "")
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        ranked.append((title_score(title, found_title), {
            "title": found_title,
            "id": entry_id,
            "pdf_url": pdf_url,
        }))
    if not ranked:
        return {}
    score, item = max(ranked, key=lambda pair: pair[0])
    return item if score >= 0.92 else {}


def candidate_pdf_urls(paper_id: str, crossref: dict, openalex: dict,
                       unpaywall: dict, semantic: dict,
                       arxiv: dict) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []

    def add(source: str, url: str | None) -> None:
        if not url:
            return
        url = url.replace("http://", "https://", 1)
        if url not in [existing for _, existing in candidates]:
            candidates.append((source, url))

    add("manual_oa", MANUAL_PDF_URLS.get(paper_id))
    add("arxiv", arxiv.get("pdf_url"))
    add("semantic_scholar", (semantic.get("openAccessPdf") or {}).get("url"))
    add("openalex_best_oa", (openalex.get("best_oa_location") or {}).get("pdf_url"))
    for location in openalex.get("locations") or []:
        add("openalex_location", location.get("pdf_url"))
    add("unpaywall_best_oa", (unpaywall.get("best_oa_location") or {}).get("url_for_pdf"))
    for location in unpaywall.get("oa_locations") or []:
        add("unpaywall_location", location.get("url_for_pdf"))
    # Keep the publisher URL last. ACM currently protects it with a browser
    # challenge, but it may still work in institutional/network environments.
    for link in crossref.get("link") or []:
        add("publisher", link.get("URL"))
    return candidates


def download_pdf(url: str, destination: Path) -> tuple[bool, str]:
    try:
        data = request(url, headers={"Accept": "application/pdf"})
    except Exception as exc:  # noqa: BLE001 - all candidates should be tried
        return False, f"{type(exc).__name__}: {exc}"
    if not data.startswith(b"%PDF-"):
        return False, f"not a PDF ({len(data)} bytes)"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return True, f"ok ({len(data)} bytes)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tracks" / "demos",
    )
    parser.add_argument("--refresh", action="store_true", help="repeat metadata lookups")
    parser.add_argument("--metadata-only", action="store_true", help="do not download PDFs")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    root = args.root.resolve()
    pdf_dir = root / "pdf"
    cache_dir = root / "metadata"
    cache_dir.mkdir(parents=True, exist_ok=True)
    accepted_cache = cache_dir / "accepted_demo.html"
    if accepted_cache.exists() and not args.refresh:
        raw_html = accepted_cache.read_text(encoding="utf-8")
    else:
        raw_html = request(ACCEPTED_URL).decode("utf-8")
        accepted_cache.write_text(raw_html, encoding="utf-8")
    papers = parse_accepted(raw_html)
    if args.limit:
        papers = papers[: args.limit]

    records = []
    for number, paper in enumerate(papers, 1):
        paper_id = paper["paper_id"]
        title = paper["title"]
        cache_path = cache_dir / f"{paper_id}.json"
        print(f"[{number}/{len(papers)}] {paper_id} {title}", flush=True)
        if cache_path.exists() and not args.refresh:
            meta = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            crossref = crossref_lookup(title)
            doi = crossref.get("DOI", "")
            openalex = openalex_lookup(doi)
            unpaywall = unpaywall_lookup(doi)
            semantic = semantic_scholar_lookup(title)
            arxiv = arxiv_lookup(title)
            meta = {
                "paper": paper,
                "crossref": crossref,
                "openalex": openalex,
                "unpaywall": unpaywall,
                "semantic_scholar": semantic,
                "arxiv": arxiv,
            }
            cache_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(0.25)

        crossref = meta.get("crossref") or {}
        openalex = meta.get("openalex") or {}
        unpaywall = meta.get("unpaywall") or {}
        semantic = meta.get("semantic_scholar") or {}
        arxiv = meta.get("arxiv") or {}
        doi = crossref.get("DOI", "")
        filename = f"{paper_id}_{slugify(title)}.pdf"
        destination = pdf_dir / filename
        status = "present" if destination.exists() else "missing"
        pdf_url = ""
        pdf_source = ""
        errors = []
        if not args.metadata_only and not destination.exists():
            for source, url in candidate_pdf_urls(
                paper_id, crossref, openalex, unpaywall, semantic, arxiv
            ):
                ok, message = download_pdf(url, destination)
                print(f"    {source}: {message}", flush=True)
                if ok:
                    status = "downloaded"
                    pdf_url = url
                    pdf_source = source
                    break
                errors.append(f"{source}: {message}")
        elif destination.exists():
            status = "present"

        if not pdf_url:
            candidates = candidate_pdf_urls(
                paper_id, crossref, openalex, unpaywall, semantic, arxiv
            )
            if candidates:
                pdf_source, pdf_url = candidates[0]
        records.append({
            "paper_id": paper_id,
            "pages": crossref.get("page", ""),
            "title": title,
            "authors": paper["authors"],
            "filename": filename,
            "doi": doi,
            "doi_url": f"https://doi.org/{doi}" if doi else "",
            "pdf_url": pdf_url,
            "pdf_source": pdf_source,
            "errors": " | ".join(errors),
            "status": status,
        })

    fields = list(records[0]) if records else []
    with (root / "index.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(records)
    print(f"\nwrote {len(records)} records to {root / 'index.tsv'}")
    print(f"PDFs present: {sum((pdf_dir / row['filename']).exists() for row in records)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
