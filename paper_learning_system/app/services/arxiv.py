from __future__ import annotations

import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.services.llm import chat_json


ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def seed_to_query(seed: str) -> str:
    seed = clean_text(seed)
    arxiv_id = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", seed)
    if arxiv_id:
        return f"id:{arxiv_id.group(1)}"

    words = [word for word in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", seed) if word.lower() not in STOP_WORDS]
    if not words:
        return f'all:"{seed}"'

    unique_words = list(dict.fromkeys(words))[:5]
    return " AND ".join(f"all:{word}" for word in unique_words)


def relaxed_query(seed: str) -> str:
    words = [word for word in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", clean_text(seed)) if word.lower() not in STOP_WORDS]
    unique_words = list(dict.fromkeys(words))[:6]
    if not unique_words:
        return f'all:"{seed}"'
    return " OR ".join(f"all:{word}" for word in unique_words)


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "using",
    "based",
    "paper",
    "study",
    "method",
}


async def mine_arxiv(seed: str, max_results: int = 8) -> list[dict[str, Any]]:
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
    max_results = min(max_results, int(os.getenv("ARXIV_MAX_RESULTS", str(max_results))))
    if os.getenv("LLM_MINING_ENABLED", "true").lower() in {"1", "true", "yes", "on"}:
        expanded = await expand_mining_queries(seed)
        results = await fetch_many(expanded, max_results=max_results, timeout=timeout)
        if results:
            return results

    query = seed_to_query(seed)
    results = await fetch_arxiv(query, max_results=max_results, timeout=timeout)
    if not results:
        results = await fetch_arxiv(relaxed_query(seed), max_results=max_results, timeout=timeout)
    return results


async def expand_mining_queries(seed: str) -> list[str]:
    system = (
        "You help mine related arXiv papers. Return strict JSON with key queries. "
        "queries must be 2 to 6 concise English search phrases, not URLs, not prose."
    )
    user = f"""
Seed paper, topic, or interest:
{seed}

Generate search phrases that can discover closely related and adjacent research papers.
"""
    result = await chat_json(system, user, task="paper-mining")
    if not result or not isinstance(result.get("queries"), list):
        return []
    queries = []
    for item in result["queries"]:
        cleaned = clean_text(str(item))
        if 3 <= len(cleaned) <= 160:
            queries.append(cleaned)
    return list(dict.fromkeys(queries))[:6]


async def fetch_many(queries: list[str], max_results: int, timeout: float) -> list[dict[str, Any]]:
    if not queries:
        return []

    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    per_query = max(3, min(max_results, 8))
    for query_text in queries:
        for query in (seed_to_query(query_text), relaxed_query(query_text)):
            try:
                results = await fetch_arxiv(query, max_results=per_query, timeout=timeout)
            except Exception:
                continue
            for paper in results:
                key = str(paper.get("external_id") or paper.get("url") or paper.get("title"))
                if key in seen:
                    continue
                seen.add(key)
                merged.append(paper)
                if len(merged) >= max_results:
                    return merged
    return merged


async def fetch_arxiv(query: str, max_results: int, timeout: float) -> list[dict[str, Any]]:
    params = {
        "search_query": query,
        "start": "0",
        "max_results": str(max_results),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    root = ET.fromstring(response.text)
    results: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", NS):
        entry_id = clean_text(entry.findtext("atom:id", default="", namespaces=NS))
        title = clean_text(entry.findtext("atom:title", default="", namespaces=NS))
        abstract = clean_text(entry.findtext("atom:summary", default="", namespaces=NS))
        published = clean_text(entry.findtext("atom:published", default="", namespaces=NS))
        authors = [
            clean_text(author.findtext("atom:name", default="", namespaces=NS))
            for author in entry.findall("atom:author", NS)
        ]
        categories = [category.attrib.get("term", "") for category in entry.findall("atom:category", NS)]
        pdf_url = ""
        for link in entry.findall("atom:link", NS):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break

        external_id = entry_id.rstrip("/").split("/")[-1]
        results.append(
            {
                "external_id": external_id,
                "source": "arxiv",
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "url": entry_id,
                "pdf_url": pdf_url,
                "published": published,
                "categories": categories,
            }
        )

    return results
