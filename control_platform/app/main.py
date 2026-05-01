from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import ProxyHandler, build_opener

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"
REGISTRY_PATH = ROOT / os.getenv("MODULE_REGISTRY", "modules/registry.json")
HEALTH_TIMEOUT_SECONDS = float(os.getenv("MODULE_HEALTH_TIMEOUT_SECONDS", "1.5"))
NO_PROXY_OPENER = build_opener(ProxyHandler({}))

app = FastAPI(title=os.getenv("PLATFORM_TITLE", "Control Platform"))
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def load_modules() -> list[dict[str, Any]]:
    with REGISTRY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def health_candidates(module: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    health_url = module.get("health_url")
    local_url = module.get("local_url")
    if health_url:
        candidates.append(str(health_url))
    if local_url and module.get("status") != "extension-point":
        candidates.append(urljoin(str(local_url).rstrip("/") + "/", "api/health"))
    return list(dict.fromkeys(candidates))


def probe_health(url: str) -> dict[str, Any]:
    try:
        with NO_PROXY_OPENER.open(url, timeout=HEALTH_TIMEOUT_SECONDS) as response:
            body = response.read(256).decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "url": url,
                "body": body,
            }
    except Exception as exc:
        return {
            "ok": False,
            "url": url,
            "error": exc.__class__.__name__,
            "detail": str(exc),
        }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"ok": "true"}


@app.get("/api/modules")
def modules() -> dict[str, Any]:
    return {"modules": load_modules()}


@app.get("/api/modules/health")
def module_health() -> dict[str, Any]:
    results = []
    for module in load_modules():
        candidates = health_candidates(module)
        if not candidates:
            results.append({
                "id": module.get("id"),
                "ok": None,
                "status": "unknown",
                "checked_url": "",
                "attempts": [],
            })
            continue

        attempts = [probe_health(url) for url in candidates]
        first_ok = next((attempt for attempt in attempts if attempt["ok"]), None)
        results.append({
            "id": module.get("id"),
            "ok": bool(first_ok),
            "status": "healthy" if first_ok else "unreachable",
            "checked_url": first_ok["url"] if first_ok else attempts[-1]["url"],
            "attempts": attempts,
        })
    return {"modules": results}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")
