from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


DATA_DIR = Path(os.getenv("LLM_MANAGER_DATA_DIR", "/app/data"))
CONFIG_PATH = DATA_DIR / "providers.json"
STATIC_DIR = Path(__file__).parent / "static"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def provider_id_from_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    return slug or "provider"


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


class ProviderIn(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=80)
    base_url: str = Field(min_length=1, max_length=300)
    api_key: str | None = Field(default=None, max_length=500)
    api_key_env: str | None = Field(default=None, max_length=80)
    default_model: str = Field(min_length=1, max_length=120)
    chat_path: str = Field(default="/chat/completions", min_length=1, max_length=160)
    enabled: bool = True

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return value

    @field_validator("chat_path")
    @classmethod
    def normalize_chat_path(cls, value: str) -> str:
        value = value.strip()
        return value if value.startswith("/") else f"/{value}"

    @field_validator("api_key_env")
    @classmethod
    def normalize_api_key_env(cls, value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip()
        if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", value):
            raise ValueError("api_key_env should look like OPENAI_API_KEY")
        return value


class Provider(ProviderIn):
    id: str
    created_at: str
    updated_at: str


class ProviderOut(BaseModel):
    id: str
    name: str
    base_url: str
    api_key_masked: str
    api_key_env: str | None
    has_env_key: bool
    default_model: str
    chat_path: str
    enabled: bool
    created_at: str
    updated_at: str


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    provider_id: str | None = None
    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int | None = Field(default=1024, ge=1, le=32768)


class ChatResponse(BaseModel):
    provider_id: str
    model: str
    content: str
    usage: dict | None = None
    raw: dict | None = None


app = FastAPI(title="LLM Manager", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def load_providers() -> list[Provider]:
    if not CONFIG_PATH.exists():
        return []
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return [Provider(**item) for item in data]


def save_providers(providers: list[Provider]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [provider.model_dump() for provider in providers]
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def public_provider(provider: Provider) -> ProviderOut:
    return ProviderOut(
        id=provider.id,
        name=provider.name,
        base_url=provider.base_url,
        api_key_masked=mask_secret(provider.api_key),
        api_key_env=provider.api_key_env,
        has_env_key=bool(provider.api_key_env and os.getenv(provider.api_key_env)),
        default_model=provider.default_model,
        chat_path=provider.chat_path,
        enabled=provider.enabled,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def find_provider(provider_id: str | None) -> Provider:
    providers = [provider for provider in load_providers() if provider.enabled]
    if not providers:
        raise HTTPException(status_code=404, detail="No enabled provider configured")
    if provider_id:
        for provider in providers:
            if provider.id == provider_id:
                return provider
        raise HTTPException(status_code=404, detail="Provider not found")
    return providers[0]


def provider_api_key(provider: Provider) -> str:
    if provider.api_key:
        return provider.api_key
    if provider.api_key_env:
        key = os.getenv(provider.api_key_env)
        if key:
            return key
    raise HTTPException(status_code=400, detail="Provider API key is not configured")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "providers": len(load_providers())}


@app.get("/api/providers", response_model=list[ProviderOut])
def list_providers() -> list[ProviderOut]:
    return [public_provider(provider) for provider in load_providers()]


@app.post("/api/providers", response_model=ProviderOut)
def upsert_provider(payload: ProviderIn) -> ProviderOut:
    providers = load_providers()
    provider_id = provider_id_from_name(payload.id or payload.name)
    existing = next((item for item in providers if item.id == provider_id), None)
    now = utc_now()

    if existing:
        existing.name = payload.name
        existing.base_url = payload.base_url
        existing.api_key = payload.api_key or existing.api_key
        existing.api_key_env = payload.api_key_env
        existing.default_model = payload.default_model
        existing.chat_path = payload.chat_path
        existing.enabled = payload.enabled
        existing.updated_at = now
        provider = existing
    else:
        provider = Provider(
            **payload.model_dump(exclude={"id"}),
            id=provider_id,
            created_at=now,
            updated_at=now,
        )
        providers.append(provider)

    save_providers(providers)
    return public_provider(provider)


@app.delete("/api/providers/{provider_id}")
def delete_provider(provider_id: str) -> dict:
    providers = load_providers()
    next_providers = [provider for provider in providers if provider.id != provider_id]
    if len(next_providers) == len(providers):
        raise HTTPException(status_code=404, detail="Provider not found")
    save_providers(next_providers)
    return {"deleted": provider_id}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    provider = find_provider(payload.provider_id)
    api_key = provider_api_key(provider)
    model = payload.model or provider.default_model
    url = f"{provider.base_url}{provider.chat_path}"
    request_payload: dict = {
        "model": model,
        "messages": [message.model_dump() for message in payload.messages],
        "temperature": payload.temperature,
    }
    if payload.max_tokens:
        request_payload["max_tokens"] = payload.max_tokens

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json=request_payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:800]
        raise HTTPException(status_code=502, detail=f"LLM provider error: {detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    choices = data.get("choices") or []
    content = ""
    if choices:
        content = choices[0].get("message", {}).get("content") or choices[0].get("text") or ""

    return ChatResponse(
        provider_id=provider.id,
        model=model,
        content=content,
        usage=data.get("usage"),
        raw=data,
    )
