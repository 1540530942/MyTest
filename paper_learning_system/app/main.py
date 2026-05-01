from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.analysis import analyze_paper, generate_practice_set
from app.services.arxiv import mine_arxiv
from app.services.db import (
    add_note,
    create_manual_paper,
    ensure_db,
    get_paper,
    list_notes,
    list_papers,
    list_practice_items,
    save_analysis,
    save_paper,
    save_practice_items,
)
from app.services.qa import answer_question
from app.services.reference_pack import import_reference_papers, load_reference_papers
from app.services.llm import chat_json


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DB_PATH = Path(os.getenv("APP_DATABASE", os.getenv("APP_DATA_DIR", "data") + "/papers.db"))

app = FastAPI(title="Online Paper Learning System")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class MineRequest(BaseModel):
    seed: str = Field(min_length=2)
    max_results: int = Field(default=8, ge=1, le=20)


class ManualPaperRequest(BaseModel):
    title: str = Field(min_length=2)
    authors: str = ""
    abstract: str = Field(default="", max_length=20000)
    url: str = ""
    pdf_url: str = ""
    published: str = ""
    source: str = "manual"


class AnalyzeRequest(BaseModel):
    force_llm: bool = False


class QuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)


class PracticeRequest(BaseModel):
    count: int = Field(default=6, ge=1, le=20)


class NoteRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20000)


class ReferenceImportRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)


class HermesChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    task: str = "paper-analysis"
    provider: str = ""
    model: str = ""


def require_token(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("API_TOKEN", "").strip()
    if not token or token == "change-me-before-public-deploy":
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Missing or invalid API token")


@app.on_event("startup")
def startup() -> None:
    ensure_db(DB_PATH)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/papers/")
def papers_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"ok": "true"}


@app.get("/api/papers", dependencies=[Depends(require_token)])
def api_list_papers() -> dict[str, Any]:
    return {"papers": list_papers(DB_PATH)}


@app.post("/api/papers", dependencies=[Depends(require_token)])
def api_create_paper(payload: ManualPaperRequest) -> dict[str, Any]:
    paper = create_manual_paper(DB_PATH, payload.model_dump())
    return {"paper": paper}


@app.get("/api/papers/{paper_id}", dependencies=[Depends(require_token)])
def api_get_paper(paper_id: int) -> dict[str, Any]:
    paper = get_paper(DB_PATH, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {
        "paper": paper,
        "notes": list_notes(DB_PATH, paper_id),
        "practice_items": list_practice_items(DB_PATH, paper_id),
    }


@app.post("/api/mine", dependencies=[Depends(require_token)])
async def api_mine(payload: MineRequest) -> dict[str, Any]:
    try:
        results = await mine_arxiv(payload.seed, max_results=payload.max_results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Paper mining source is unreachable: {exc}") from exc
    return {"results": results}


@app.get("/api/reference-papers", dependencies=[Depends(require_token)])
def api_reference_papers() -> dict[str, Any]:
    return {"papers": load_reference_papers()}


@app.post("/api/reference-papers/import", dependencies=[Depends(require_token)])
def api_import_reference_papers(payload: ReferenceImportRequest) -> dict[str, Any]:
    imported = import_reference_papers(DB_PATH, ids=payload.ids or None)
    return {"papers": imported}


@app.post("/api/papers/import", dependencies=[Depends(require_token)])
def api_import_paper(payload: dict[str, Any]) -> dict[str, Any]:
    paper = save_paper(DB_PATH, payload)
    return {"paper": paper}


@app.post("/api/papers/{paper_id}/analyze", dependencies=[Depends(require_token)])
async def api_analyze_paper(paper_id: int, payload: AnalyzeRequest) -> dict[str, Any]:
    paper = get_paper(DB_PATH, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    analysis = await analyze_paper(paper, force_llm=payload.force_llm)
    save_analysis(DB_PATH, paper_id, analysis)
    return {"analysis": analysis}


@app.post("/api/papers/{paper_id}/question", dependencies=[Depends(require_token)])
async def api_question(paper_id: int, payload: QuestionRequest) -> dict[str, Any]:
    paper = get_paper(DB_PATH, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    answer = await answer_question(paper, payload.question)
    return {"answer": answer}


@app.post("/api/papers/{paper_id}/practice", dependencies=[Depends(require_token)])
async def api_practice(paper_id: int, payload: PracticeRequest) -> dict[str, Any]:
    paper = get_paper(DB_PATH, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    items = await generate_practice_set(paper, count=payload.count)
    save_practice_items(DB_PATH, paper_id, items)
    return {"items": items}


@app.post("/api/papers/{paper_id}/notes", dependencies=[Depends(require_token)])
def api_add_note(paper_id: int, payload: NoteRequest) -> dict[str, Any]:
    paper = get_paper(DB_PATH, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    note = add_note(DB_PATH, paper_id, payload.content)
    return {"note": note}


@app.get("/api/hermes/providers")
async def api_hermes_providers() -> dict[str, Any]:
    hermes_url = os.getenv("HERMES_URL", "").strip().rstrip("/")
    if not hermes_url:
        return {"providers": [], "task_routes": {}}

    timeout = float(os.getenv("HERMES_HTTP_TIMEOUT_SECONDS", os.getenv("HTTP_TIMEOUT_SECONDS", "45")))
    headers = {"Content-Type": "application/json"}
    token = os.getenv("HERMES_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{hermes_url}/api/providers", headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception:
        return {"providers": [], "task_routes": {}}


@app.post("/api/hermes/chat")
async def api_hermes_chat(payload: HermesChatRequest) -> dict[str, Any]:
    system = (
        "You are Hermes inside an online paper learning system. "
        "Help the user mine papers, explain research ideas, compare methods, "
        "design reading plans, and generate active-recall questions. "
        "Return strict JSON with keys: mode, answer, suggestions."
    )
    result = await chat_json(
        system,
        payload.message,
        task=payload.task,
        provider=payload.provider,
        model=payload.model,
    )
    if result:
        return {"answer": result}
    return {
        "answer": {
            "mode": "local-fallback",
            "answer": "Hermes is reachable from the paper app, but no provider produced a response. Check provider keys or ask about a saved paper with the local tools.",
            "suggestions": [
                "Try a narrower paper topic.",
                "Check /root/control_platform/test_hermes_providers.sh on the server.",
                "Use the paper analysis and Q&A buttons for saved papers.",
            ],
        }
    }
