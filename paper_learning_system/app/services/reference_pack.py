from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.services.db import save_paper


REFERENCE_PATH = Path(__file__).resolve().parents[1] / "data" / "reference_papers.json"


def _date_key(item: dict[str, Any]) -> tuple[str, str]:
    published = str(item.get("published") or "9999-12-31")
    return published[:10], str(item.get("title") or "")


def load_reference_papers() -> list[dict[str, Any]]:
    with REFERENCE_PATH.open("r", encoding="utf-8") as handle:
        papers = json.load(handle)
    return sorted(papers, key=_date_key)


def reference_to_paper_payload(reference: dict[str, Any]) -> dict[str, Any]:
    tags = [
        reference.get("category", ""),
        reference.get("role", ""),
        reference.get("source_pack", ""),
    ]
    tags = [str(tag).strip() for tag in tags if str(tag).strip()]
    arxiv_id = re.sub(r"v\d+$", "", str(reference.get("id") or ""))
    return {
        "external_id": reference.get("id"),
        "source": "reference-pack",
        "title": reference.get("title", "Untitled paper"),
        "authors": reference.get("authors", ""),
        "abstract": reference.get("summary", ""),
        "url": reference.get("url", ""),
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else "",
        "published": reference.get("published", ""),
        "categories": tags,
    }


def import_reference_papers(db_path: Path, ids: list[str] | None = None) -> list[dict[str, Any]]:
    wanted = set(ids or [])
    imported = []
    for reference in load_reference_papers():
        if wanted and reference.get("id") not in wanted:
            continue
        imported.append(save_paper(db_path, reference_to_paper_payload(reference)))
    return imported
