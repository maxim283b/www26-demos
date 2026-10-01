#!/usr/bin/env python3
"""Add manually verified paper and code links to missing-track indexes."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEXES = (
    ROOT / "tracks/research/user-modeling-personalization-recommendation/index.tsv",
    ROOT / "tracks/research/web-mining-content-analysis/index.tsv",
    ROOT / "tracks/industry/index.tsv",
    ROOT / "tracks/short-papers/index.tsv",
    ROOT / "tracks/web4good/index.tsv",
)
CODE = {
    "10.1145/3774904.3792070": "https://github.com/Yu-Qi-hang/ThinkRec",
    "10.1145/3774904.3792092": "https://github.com/guanwei49/SEAR",
    "10.1145/3774904.3792123": "https://github.com/htired/ISRF",
    "10.1145/3774904.3792124": "https://github.com/USTC-StarTeam/Taesar",
    "10.1145/3774904.3792148": "https://github.com/HCoder-PY/SEDIRec_WWW2026",
    "10.1145/3774904.3792456": "https://github.com/Applied-Machine-Learning-Lab/WWW2026_SAGE-LLM",
    "10.1145/3774904.3792500": "https://github.com/whu-totemdb/LoRA-E2",
    "10.1145/3774904.3792868": "https://github.com/MarcT0K/Fedivertex-Python",
    "10.1145/3774904.3792887": "https://github.com/cisnlp/GlotWeb",
    "10.1145/3774904.3792929": "https://github.com/SAGE-RAI",
}
PAPERS = {
    "10.1145/3774904.3792086": "https://research.aalto.fi/files/226844175/Quantum-enhanced_Representation_Learning_and_Matching_Learning_for_Recommendation.pdf",
    "10.1145/3774904.3792123": "https://arxiv.org/pdf/2603.13934",
    "10.1145/3774904.3792124": "https://arxiv.org/pdf/2602.22743",
    "10.1145/3774904.3792148": "https://arxiv.org/pdf/2601.18998",
    "10.1145/3774904.3792500": "https://sheng.whu.edu.cn/papers/26www.pdf",
    "10.1145/3774904.3792819": "https://scholars.cityu.edu.hk/files/496945877/491109912.pdf",
    "10.1145/3774904.3792794": "https://scholars.cityu.edu.hk/files/495507072/491107809.pdf",
    "10.1145/3774904.3792868": "https://arxiv.org/pdf/2505.20882",
    "10.1145/3774904.3792929": "https://oro.open.ac.uk/108348/2/Kwarteng_SAGE_RAI_srp620.pdf",
    "10.1145/3774904.3793002": "https://wangdan.people.ust.hk/Publication/WWW26-PPA.pdf",
    "10.1145/3774904.3793051": "https://wangdan.people.ust.hk/Publication/WWW26-CIF.pdf",
}
FIELDS = ["paper_id", "track", "title", "doi", "doi_url", "open_url", "source_type", "code_url"]


def main() -> int:
    for path in INDEXES:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        for row in rows:
            row["code_url"] = CODE.get(row["doi"], row.get("code_url", ""))
            if row["doi"] in PAPERS:
                row["open_url"] = PAPERS[row["doi"]]
                row["source_type"] = "open_pdf"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, delimiter="\t", fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
