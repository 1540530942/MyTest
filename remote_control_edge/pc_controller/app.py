from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from serial import SerialException

from serial_client import create_client

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
SERIAL_PORT = os.getenv("ARDUINO_PORT", "COM3").strip()
BAUDRATE = int(os.getenv("ARDUINO_BAUDRATE", "115200").strip())
API_TOKEN = os.getenv("ARDUINO_API_TOKEN", "").strip()

app = FastAPI(title="Arduino Remote LED Controller")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
client = create_client(SERIAL_PORT, BAUDRATE)


class CommandResponse(BaseModel):
    ok: bool
    command: str
    response: str
    serial_port: str


class HealthResponse(BaseModel):
    ok: bool
    serial_port: str
    token_required: bool


def require_token(x_api_token: str | None, token: str | None) -> None:
    if not API_TOKEN:
        return

    provided = x_api_token or token
    if provided != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


def run_command(command: str) -> CommandResponse:
    try:
        response = client.send_command(command)
    except (SerialException, FileNotFoundError, PermissionError, TimeoutError) as exc:
        raise HTTPException(status_code=500, detail=f"Serial communication failed: {exc}") from exc

    return CommandResponse(
        ok=response.startswith("OK") or response.startswith("STATUS"),
        command=command,
        response=response,
        serial_port=SERIAL_PORT,
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        serial_port=SERIAL_PORT,
        token_required=bool(API_TOKEN),
    )


@app.get("/status", response_model=CommandResponse)
def status(
    x_api_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> CommandResponse:
    require_token(x_api_token, token)
    return run_command("STATUS")


@app.post("/led/on", response_model=CommandResponse)
def led_on(
    x_api_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> CommandResponse:
    require_token(x_api_token, token)
    return run_command("LED_ON")


@app.post("/led/off", response_model=CommandResponse)
def led_off(
    x_api_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> CommandResponse:
    require_token(x_api_token, token)
    return run_command("LED_OFF")
