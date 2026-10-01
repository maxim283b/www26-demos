#!/usr/bin/env python3
"""Convert WebConf PDFs into one Markdown directory per paper.

By default, reads the demo corpus from ``tracks/demos/pdf`` and writes to
``tracks/demos/md``. Other tracks can be selected with ``--input`` and
``--output``. The output follows
marker's own naming convention:

    md/
      42333_DTECT_Dynamic_Topic_Explorer_Context_Tracker/
        42333_DTECT_Dynamic_Topic_Explorer_Context_Tracker.md
        42333_DTECT_Dynamic_Topic_Explorer_Context_Tracker_meta.json
        _page_0_Figure_1.jpeg
        ...
      manifest.jsonl
      _logs/etl_<timestamp>.log

Re-runs are incremental: a paper that already has a non-empty .md is skipped
unless --force is given, so an interrupted run can just be restarted, and a
paper that failed is retried on the next run.

Conversion happens in-process (models load once, papers convert sequentially)
rather than through the `marker` batch CLI, which unconditionally spawns a
llama.cpp VLM server that fast mode does not need.

Requires marker-pdf (declared in pyproject.toml).  This corpus uses ``--no-ocr``
because the publisher PDFs have embedded text; the option avoids unnecessary
OCR/VLM work while preserving the prose used in the analysis.

marker can live either in this project's environment (uv sync, then run with
`uv run ./etl.py`) or in a standalone tool environment (uv tool install
marker-pdf, then run `./etl.py` directly). If the interpreter running this
script cannot import marker, it re-execs itself under the one that can.

Usage:
    ./etl.py                                              # convert the demo corpus
    ./etl.py --limit 3                                    # smoke test
    ./etl.py --force                                      # reconvert everything
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re

# Must be set before marker (and therefore torch) is imported: transformers uses
# a handful of ops MPS lacks, and they need to fall back to CPU.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GLOG_minloglevel", "2")

import shutil  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

# A .md smaller than this means marker produced a stub, not a paper.
MIN_MD_BYTES = 512

# Guard against an exec loop if the re-exec'd interpreter still lacks marker.
REEXEC_FLAG = "WEBCONF_ETL_REEXEC"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(
        description="PDF -> per-paper markdown directories, via marker.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--input",
        type=Path,
        default=here / "tracks" / "demos" / "pdf",
        help="folder holding the PDFs",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=here / "tracks" / "demos" / "md",
        help="destination for the per-paper directories",
    )
    p.add_argument(
        "--index",
        type=Path,
        default=None,
        help="TSV with paper_id/title/doi_url metadata "
        "(default: index.tsv beside the PDFs or one level up)",
    )
    p.add_argument(
        "--mode",
        choices=("fast", "balanced"),
        default=None,
        help="marker conversion mode (default: marker picks by device -- fast on "
        "CPU/MPS, balanced on GPU; balanced needs a llama.cpp server)",
    )
    p.add_argument(
        "--no-ocr",
        action="store_true",
        help="extract from the embedded PDF text layer and disable OCR",
    )
    p.add_argument("--limit", type=int, default=None, help="convert at most N papers")
    p.add_argument(
        "--force", action="store_true", help="reconvert papers that already have markdown"
    )
    p.add_argument(
        "--dry-run", action="store_true", help="report what would be converted, then exit"
    )
    args = p.parse_args(argv)

    args.input = args.input.resolve()
    args.output = args.output.resolve()
    if args.index is None:
        beside = args.input / "index.tsv"
        args.index = beside if beside.exists() else args.input.parent / "index.tsv"
    return args


def ensure_marker_importable() -> None:
    """Re-exec under the interpreter that owns marker, if this one doesn't.

    marker is typically installed as a uv tool, i.e. into its own venv that is
    not on the default python's path. The console scripts it installs point at
    that venv's interpreter, so we read it off the `marker_single` shebang.
    """
    try:
        import marker  # noqa: F401
        return
    except ImportError:
        pass

    if os.environ.get(REEXEC_FLAG):
        sys.exit("re-exec'd interpreter still cannot import marker; aborting")

    script = shutil.which("marker_single") or str(Path.home() / ".local/bin/marker_single")
    interpreter = None
    try:
        with open(script, encoding="utf-8") as fh:
            first = fh.readline()
        if first.startswith("#!"):
            interpreter = first[2:].strip()
    except OSError:
        pass

    if not interpreter or not os.path.isfile(interpreter):
        sys.exit(
            "marker is not importable and its interpreter could not be found.\n"
            "Install it with:  uv tool install marker-pdf"
        )

    os.environ[REEXEC_FLAG] = "1"
    os.execv(interpreter, [interpreter, os.path.abspath(__file__), *sys.argv[1:]])


def load_index(index_path: Path) -> dict[str, dict[str, str]]:
    """Map both PDF filename and paper id to metadata rows when available."""
    if not index_path.exists():
        return {}
    with index_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("filename"):
            index[row["filename"]] = row
        if row.get("paper_id"):
            index[row["paper_id"]] = row
    return index


def paper_dir(output: Path, pdf: Path) -> Path:
    # Windows still imposes a 260-character limit in some dependencies.  The
    # accepted-paper id is unique and keeps both output paths and links short.
    return output / pdf.stem.split("_", 1)[0]


def markdown_path(output: Path, pdf: Path) -> Path:
    return paper_dir(output, pdf) / f"{pdf.stem.split('_', 1)[0]}.md"


def is_converted(output: Path, pdf: Path) -> bool:
    md = markdown_path(output, pdf)
    return md.exists() and md.stat().st_size >= MIN_MD_BYTES


def remove_review_line_numbers(path: Path) -> None:
    """Drop margin line numbers from review manuscripts after Marker export.

    Some author copies render red review line numbers as selectable text.
    Marker then emits them as many standalone numeric lines.  We only enable
    this cleanup when the opening block contains at least five such lines, so
    normal page numbers, equations, and numbered examples remain untouched in
    ordinary proceedings PDFs.
    """
    text = path.read_text(encoding="utf-8")
    numeric_line = re.compile(r"(?m)^[ \t]*\d+(?:[ \t]+\d+)*[ \t]*$")
    if len(numeric_line.findall(text[:800])) < 5:
        return
    cleaned = numeric_line.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).lstrip()
    path.write_text(cleaned, encoding="utf-8")


def convert_all(todo: list[Path], args: argparse.Namespace, log_path: Path) -> None:
    """Convert each PDF, loading marker's models once for the whole run.

    One paper's failure is logged and the run continues; failures are reported
    at the end and picked up again by the next run.
    """
    import logging

    from marker.config.parser import ConfigParser
    from marker.logger import configure_logging
    from marker.models import create_model_dict
    from marker.output import save_output

    configure_logging()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(handler)

    options = {"output_dir": str(args.output), "output_format": "markdown"}
    if args.mode:
        options["mode"] = args.mode
    if args.no_ocr:
        options["disable_ocr"] = True
    config_parser = ConfigParser(options)
    converter_cls = config_parser.get_converter_cls()

    print(f"loading models (log: {log_path})", flush=True)
    models = create_model_dict()

    run_start = time.time()
    for i, pdf in enumerate(todo, start=1):
        print(f"[{i}/{len(todo)}] {pdf.name}", flush=True)
        started = time.time()
        try:
            converter = converter_cls(
                config=config_parser.generate_config_dict(),
                artifact_dict=models,
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
                llm_service=config_parser.get_llm_service(),
            )
            rendered = converter(str(pdf))
            out_folder = paper_dir(args.output, pdf)
            out_folder.mkdir(parents=True, exist_ok=True)
            save_output(rendered, str(out_folder), pdf.stem.split("_", 1)[0])
            remove_review_line_numbers(markdown_path(args.output, pdf))
            del rendered, converter
            print(f"           ok  {time.time() - started:.1f}s", flush=True)
        except Exception as exc:  # noqa: BLE001 - one bad PDF must not stop the run
            logging.getLogger(__name__).exception("failed to convert %s", pdf.name)
            print(f"           FAILED  {type(exc).__name__}: {exc}", flush=True)

    print(f"\nconversion took {(time.time() - run_start) / 60:.1f} min", flush=True)


def write_manifest(pdfs: list[Path], attempted: set[Path], args: argparse.Namespace,
                   index: dict[str, dict[str, str]]) -> list[dict]:
    """Record one row per PDF describing its converted output.

    status is `ok`, `failed` (attempted this run, no usable markdown) or
    `pending` (never attempted, e.g. skipped by --limit).
    """
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    records = []
    for pdf in sorted(pdfs):
        meta = index.get(pdf.name) or index.get(pdf.stem.split("_", 1)[0], {})
        directory = paper_dir(args.output, pdf)
        md = markdown_path(args.output, pdf)
        ok = is_converted(args.output, pdf)
        images = (
            sorted(p.name for p in directory.iterdir()
                   if p.suffix.lower() in {".jpeg", ".jpg", ".png", ".webp"})
            if directory.is_dir() else []
        )
        if ok:
            status = "ok"
        elif pdf in attempted:
            status = "failed"
        else:
            status = "pending"
        records.append({
            "paper_id": meta.get("paper_id"),
            "title": meta.get("title"),
            "pages": meta.get("pages"),
            "doi_url": meta.get("doi_url"),
            "pdf": pdf.name,
            "dir": str(directory.relative_to(args.output)),
            "markdown": md.name if ok else None,
            "md_bytes": md.stat().st_size if md.exists() else 0,
            "images": len(images),
            "status": status,
            "checked_at": now,
        })

    manifest = args.output / "manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return records


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.input.is_dir():
        sys.exit(f"input folder does not exist: {args.input}")

    pdfs = sorted(p for p in args.input.glob("*.pdf") if p.is_file())
    if not pdfs:
        sys.exit(f"no PDFs found in {args.input}")

    index = load_index(args.index)
    # Only filename keys can be checked directly.  Newer indexes identify a
    # paper by id and intentionally let the downloader choose a safe suffix.
    missing_pdf = [
        name for name in index
        if name.lower().endswith(".pdf") and not (args.input / name).exists()
    ]

    done = [p for p in pdfs if is_converted(args.output, p)]
    todo = pdfs if args.force else [p for p in pdfs if p not in set(done)]
    if args.limit:
        todo = todo[: args.limit]

    print(f"input   {args.input}")
    print(f"output  {args.output}")
    print(f"papers  {len(pdfs)} PDFs, {len(done)} already converted, "
          f"{len(todo)} to convert now")
    if missing_pdf:
        print(f"warning {len(missing_pdf)} rows in {args.index.name} have no PDF on disk:")
        for name in missing_pdf:
            print(f"          {name}")

    if args.dry_run:
        for pdf in todo:
            print(f"  would convert  {pdf.name}")
        return 0

    args.output.mkdir(parents=True, exist_ok=True)

    if todo:
        ensure_marker_importable()
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        convert_all(todo, args, args.output / "_logs" / f"etl_{stamp}.log")
    else:
        print("\nnothing to convert")

    records = write_manifest(pdfs, set(todo), args, index)
    counts = {"ok": 0, "failed": 0, "pending": 0}
    for record in records:
        counts[record["status"]] += 1

    print(f"\nconverted {counts['ok']}/{len(records)} papers -> {args.output}")
    print(f"manifest  {args.output / 'manifest.jsonl'}")
    if counts["pending"]:
        print(f"pending   {counts['pending']} not attempted yet (run again without --limit)")
    if counts["failed"]:
        print(f"\n{counts['failed']} failed (re-run this script to retry just these):")
        for record in records:
            if record["status"] == "failed":
                print(f"  {record['pdf']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
