from __future__ import annotations

import re
from typing import Any

from app.services.llm import chat_json


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text or "").strip())
    return [part.strip() for part in parts if len(part.strip()) > 20]


def keywords(text: str, limit: int = 12) -> list[str]:
    stop = {
        "this",
        "that",
        "with",
        "from",
        "using",
        "based",
        "paper",
        "model",
        "models",
        "method",
        "methods",
        "results",
        "approach",
        "learning",
        "data",
        "show",
        "propose",
        "proposed",
    }
    counts: dict[str, int] = {}
    for word in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", text.lower()):
        if word not in stop:
            counts[word] = counts.get(word, 0) + 1
    return [word for word, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def fallback_analysis(paper: dict[str, Any]) -> dict[str, Any]:
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    sent = sentences(abstract)
    keys = keywords(f"{title} {abstract}")
    return {
        "mode": "local-fallback",
        "one_sentence": sent[0] if sent else f"This paper studies: {title}",
        "background": sent[:2] or ["Background is not available in the saved abstract."],
        "core_problem": sent[1] if len(sent) > 1 else "Identify the main research problem from the title and abstract.",
        "method": sent[2] if len(sent) > 2 else "The method is not explicit in the saved abstract.",
        "contributions": sent[3:6] or ["Extract the main contribution after reading the full paper."],
        "limitations": [
            "The local fallback cannot verify experiments beyond the abstract.",
            "Read the full paper to inspect assumptions, datasets, baselines, and failure cases.",
        ],
        "keywords": keys,
        "reading_plan": [
            "Read the abstract and introduction to locate the problem statement.",
            "Skim figures, method overview, and experiments.",
            "Read limitations and compare with related work.",
            "Write three takeaways and two open questions.",
        ],
    }


async def analyze_paper(paper: dict[str, Any], force_llm: bool = False) -> dict[str, Any]:
    system = (
        "You are a careful research-paper tutor. Return strict JSON with keys: "
        "mode, one_sentence, background, core_problem, method, contributions, "
        "limitations, keywords, reading_plan."
    )
    user = f"""
Title: {paper.get("title", "")}
Authors: {paper.get("authors", "")}
Published: {paper.get("published", "")}
Abstract:
{paper.get("abstract", "")}
"""
    if force_llm:
        result = await chat_json(system, user, task="paper-analysis")
        if result:
            result["mode"] = "llm"
            return result
    else:
        result = await chat_json(system, user, task="paper-analysis")
        if result:
            result["mode"] = "llm"
            return result

    return fallback_analysis(paper)


def fallback_practice(paper: dict[str, Any], count: int = 6) -> list[dict[str, str]]:
    analysis = paper.get("analysis")
    if isinstance(analysis, str):
        analysis = None
    abstract_sentences = sentences(paper.get("abstract", ""))
    keys = keywords(f"{paper.get('title', '')} {paper.get('abstract', '')}", limit=8)
    items = [
        {
            "kind": "summary",
            "question": "Can you explain the paper in one sentence?",
            "answer": (analysis or {}).get("one_sentence") or (abstract_sentences[0] if abstract_sentences else paper.get("title", "")),
        },
        {
            "kind": "problem",
            "question": "What research problem is this paper trying to solve?",
            "answer": (analysis or {}).get("core_problem") or "Use the abstract and introduction to identify the core research gap.",
        },
        {
            "kind": "method",
            "question": "What is the main method or technical idea?",
            "answer": (analysis or {}).get("method") or "The saved abstract does not make the method explicit.",
        },
        {
            "kind": "limitation",
            "question": "What limitation should you check while reading?",
            "answer": "Check datasets, assumptions, baselines, ablations, and whether the claims exceed the evidence.",
        },
    ]
    for key in keys:
        items.append(
            {
                "kind": "concept",
                "question": f"What role does '{key}' play in this paper?",
                "answer": f"Locate '{key}' in the abstract or full text, then connect it to the problem, method, or evaluation.",
            }
        )
    return items[:count]


async def generate_practice_set(paper: dict[str, Any], count: int = 6) -> list[dict[str, str]]:
    system = (
        "You generate active-recall study questions for a research paper. "
        "Return strict JSON with key items. items is a list of objects with kind, question, answer."
    )
    user = f"""
Generate {count} concise question-answer pairs.
Title: {paper.get("title", "")}
Abstract: {paper.get("abstract", "")}
Analysis: {paper.get("analysis", "")}
"""
    result = await chat_json(system, user, task="practice")
    if result and isinstance(result.get("items"), list):
        return [
            {
                "kind": str(item.get("kind", "concept")),
                "question": str(item.get("question", "")),
                "answer": str(item.get("answer", "")),
            }
            for item in result["items"][:count]
            if item.get("question") and item.get("answer")
        ]
    return fallback_practice(paper, count=count)
