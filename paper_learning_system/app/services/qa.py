from __future__ import annotations

from typing import Any

from app.services.analysis import fallback_analysis, keywords, sentences
from app.services.llm import chat_json


def local_answer(paper: dict[str, Any], question: str) -> dict[str, Any]:
    abstract = paper.get("abstract", "")
    sent = sentences(abstract)
    q_words = set(keywords(question, limit=10))
    ranked = []
    for sentence in sent:
        s_words = set(keywords(sentence, limit=20))
        score = len(q_words & s_words)
        ranked.append((score, sentence))
    ranked.sort(key=lambda item: item[0], reverse=True)
    evidence = [sentence for score, sentence in ranked[:3] if score > 0] or sent[:2]
    analysis = paper.get("analysis") if isinstance(paper.get("analysis"), dict) else fallback_analysis(paper)
    return {
        "mode": "local-fallback",
        "answer": " ".join(evidence) if evidence else analysis["one_sentence"],
        "evidence": evidence,
        "next_step": "Open the full paper and verify this answer against the method, experiments, and limitations.",
    }


async def answer_question(paper: dict[str, Any], question: str) -> dict[str, Any]:
    system = (
        "You answer questions about a research paper using only the supplied title, abstract, "
        "analysis, and notes. Return strict JSON with keys: mode, answer, evidence, next_step."
    )
    user = f"""
Question: {question}

Title: {paper.get("title", "")}
Authors: {paper.get("authors", "")}
Abstract:
{paper.get("abstract", "")}
Analysis:
{paper.get("analysis", "")}
"""
    result = await chat_json(system, user, task="paper-qa")
    if result:
        result["mode"] = "llm"
        return result
    return local_answer(paper, question)
