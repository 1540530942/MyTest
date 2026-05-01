from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
LATEST_IMAGE = DATA_DIR / "latest.jpg"
STATE_FILE = DATA_DIR / "control_state.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_TOKEN = secrets.compare_digest


app = FastAPI(title="TurboPi Camera Snapshot", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


state = {
    "task": None,
    "updated_at": 0.0,
}

latest_meta = {
    "has_image": False,
    "updated_at": 0.0,
    "device_id": "",
    "frame_id": "",
    "content_length": 0,
    "task_id": "",
}


def require_token(x_camera_token: str | None) -> None:
    token_file = BASE_DIR / ".camera_token"
    data_token_file = DATA_DIR / ".camera_token"
    expected = ""
    if data_token_file.exists():
        expected = data_token_file.read_text(encoding="utf-8").strip()
    elif token_file.exists():
        expected = token_file.read_text(encoding="utf-8").strip()
    if not expected:
        return
    if not x_camera_token or not UPLOAD_TOKEN(x_camera_token, expected):
        raise HTTPException(status_code=401, detail="invalid camera token")


def refresh_task_status() -> None:
    task = state.get("task")
    if not isinstance(task, dict):
        return
    if task.get("status") in {"complete", "expired"}:
        return
    if time.time() > float(task.get("deadline_at") or 0):
        task["status"] = "expired"
        state["updated_at"] = time.time()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"status": "ok", "has_image": latest_meta["has_image"]}


@app.get("/api/control")
def get_control() -> dict[str, object]:
    refresh_task_status()
    return dict(state)


@app.post("/api/capture")
def create_capture_task(payload: dict[str, object]) -> dict[str, object]:
    mode = str(payload.get("mode") or "single").strip().lower()
    now = time.time()
    if mode == "single":
        max_frames = 1
        duration_seconds = 10
        interval_ms = 0
    elif mode == "continuous":
        try:
            interval_ms = int(payload.get("interval_ms") or 1000)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="interval_ms must be an integer")
        interval_ms = max(200, min(interval_ms, 10000))
        max_frames = 0
        duration_seconds = 24 * 60 * 60
    else:
        raise HTTPException(status_code=400, detail="mode must be single or continuous")

    task = {
        "id": f"{int(now * 1000)}-{secrets.token_hex(3)}",
        "mode": mode,
        "status": "pending",
        "requested_at": now,
        "deadline_at": now + duration_seconds,
        "max_frames": max_frames,
        "uploaded_frames": 0,
        "interval_ms": interval_ms,
    }
    state["task"] = task
    state["updated_at"] = time.time()
    return {"ok": True, "task": task}


@app.post("/api/stop")
def stop_capture_task() -> dict[str, object]:
    task = state.get("task")
    if isinstance(task, dict) and task.get("status") not in {"complete", "expired", "stopped"}:
        task["status"] = "stopped"
    state["updated_at"] = time.time()
    return {"ok": True, "task": state.get("task")}


@app.post("/api/frame")
async def upload_frame(
    request: Request,
    x_device_id: Annotated[str, Header()] = "turbopi",
    x_frame_id: Annotated[str, Header()] = "",
    x_task_id: Annotated[str, Header()] = "",
    x_camera_token: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    require_token(x_camera_token)

    content_type = (request.headers.get("content-type") or "").lower()
    if content_type not in {"image/jpeg", "image/jpg"}:
        raise HTTPException(status_code=415, detail="only JPEG frames are accepted")

    raw = await request.body()
    if not raw:
        raise HTTPException(status_code=400, detail="empty image")
    if len(raw) > 4 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="image too large")

    tmp_file = DATA_DIR / "latest.tmp"
    tmp_file.write_bytes(raw)
    tmp_file.replace(LATEST_IMAGE)

    latest_meta.update(
        {
            "has_image": True,
            "updated_at": time.time(),
            "device_id": x_device_id,
            "frame_id": x_frame_id,
            "task_id": x_task_id,
            "content_length": len(raw),
        }
    )

    task = state.get("task")
    if isinstance(task, dict) and x_task_id and x_task_id == task.get("id"):
        if time.time() > float(task.get("deadline_at") or 0):
            task["status"] = "expired"
        else:
            task["uploaded_frames"] = int(task.get("uploaded_frames") or 0) + 1
            max_frames = int(task.get("max_frames") or 0)
            task["status"] = "complete" if max_frames and task["uploaded_frames"] >= max_frames else "active"
        state["updated_at"] = time.time()

    return {"ok": True, **latest_meta}


@app.get("/api/latest")
def latest() -> dict[str, object]:
    return dict(latest_meta)


@app.get("/api/latest.jpg", response_model=None)
def latest_image():
    if not LATEST_IMAGE.exists():
        return JSONResponse({"error": "no_image"}, status_code=404)
    return FileResponse(
        LATEST_IMAGE,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )
