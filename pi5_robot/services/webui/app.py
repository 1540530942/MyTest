from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.harnessd.executor import HarnessExecutor
from services.harnessd.logger import EpisodeLogger
from services.robotd.simulator import RobotCommandError, RobotController
from services.visiond.simulator import VisionService


STATIC_DIR = ROOT / "services" / "webui" / "static"

app = FastAPI(title="Pi5 Harness Robot", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

robot = RobotController()
vision = VisionService(ROOT)
logger = EpisodeLogger(ROOT)
harness = HarnessExecutor(robot, vision, logger)


class MoveRequest(BaseModel):
    direction: str = Field("forward", pattern="^(forward|backward)$")
    distance_cm: float = Field(10, ge=1, le=50)
    max_speed_mps: float = Field(0.2, ge=0.05, le=0.3)
    stop_if_obstacle: bool = True


class RotateRequest(BaseModel):
    angle_deg: float = Field(..., ge=-90, le=90)


class ServoRequest(BaseModel):
    pan_deg: float | None = Field(None, ge=-90, le=90)
    tilt_deg: float | None = Field(None, ge=-35, le=45)


class TaskRequest(BaseModel):
    task: str = Field(..., min_length=1)
    mode: str = "supervised_autonomy"


def command_response(fn: Any) -> dict[str, Any]:
    try:
        return {"ok": True, "state": fn()}
    except RobotCommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "mode": "simulation",
        "service": "pi5_robot",
    }


@app.get("/api/robot/state")
def robot_state() -> dict[str, Any]:
    return robot.snapshot()


@app.get("/api/robot/safety")
def robot_safety() -> dict[str, Any]:
    return robot.safety()


@app.post("/api/robot/move")
def robot_move(payload: MoveRequest) -> dict[str, Any]:
    return command_response(
        lambda: robot.move(
            payload.direction,
            payload.distance_cm,
            payload.max_speed_mps,
            payload.stop_if_obstacle,
        )
    )


@app.post("/api/robot/rotate")
def robot_rotate(payload: RotateRequest) -> dict[str, Any]:
    return command_response(lambda: robot.rotate(payload.angle_deg))


@app.post("/api/robot/stop")
def robot_stop() -> dict[str, Any]:
    return {"ok": True, "state": robot.stop("api")}


@app.post("/api/robot/servo/pan_tilt")
def robot_servo(payload: ServoRequest) -> dict[str, Any]:
    return {"ok": True, "state": robot.pan_tilt(payload.pan_deg, payload.tilt_deg)}


@app.post("/api/camera/capture")
def camera_capture() -> dict[str, Any]:
    result = vision.capture("manual")
    logger.record("manual", "tool_call", tool="capture_image", result=result)
    return result


@app.post("/api/vision/describe")
def vision_describe() -> dict[str, Any]:
    return vision.describe_scene(robot.snapshot())


@app.post("/api/task")
def task_submit(payload: TaskRequest) -> dict[str, Any]:
    try:
        return harness.submit(payload.task, payload.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/task/{task_id}/status")
def task_status(task_id: str) -> dict[str, Any]:
    return harness.status(task_id)


@app.get("/api/task/{task_id}/trace")
def task_trace(task_id: str) -> dict[str, Any]:
    return {"task_id": task_id, "events": harness.trace(task_id)}


@app.post("/api/task/{task_id}/cancel")
def task_cancel(task_id: str) -> dict[str, Any]:
    return harness.cancel(task_id)
