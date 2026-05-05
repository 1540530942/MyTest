from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse, urlunparse

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


DATA_DIR = Path(os.getenv("LLM_MANAGER_DATA_DIR", "/app/data"))
CONFIG_PATH = DATA_DIR / "providers.json"
STATIC_DIR = Path(__file__).parent / "static"


def default_registry_path() -> Path:
    container_path = Path("/app/control_platform/modules/registry.json")
    if container_path.exists():
        return container_path
    return Path(__file__).resolve().parents[2] / "control_platform" / "modules" / "registry.json"


REGISTRY_PATH = Path(os.getenv("WEB_MANAGER_REGISTRY_PATH", default_registry_path()))


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


class ModuleStatus(BaseModel):
    id: str
    name: str
    summary: str = ""
    public_url: str = ""
    local_url: str = ""
    service_url: str = ""
    health_url: str = ""
    image: str = ""
    status: str = ""
    connection_state: Literal["online", "offline", "unknown", "not_configured"]
    connection_detail: str = ""
    current_progress: str = ""
    next_step: str = ""
    capabilities: list[str] = []
    checked_at: str


app = FastAPI(title="Web Manager", version="0.2.0")
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


def load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    with REGISTRY_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []


def module_health_url(module: dict) -> str:
    health_url = str(module.get("health_url") or "")
    local_url = str(module.get("local_url") or "").rstrip("/")
    if not health_url or not local_url:
        return health_url

    if str(REGISTRY_PATH).startswith("/app/"):
        return health_url

    parsed_health = urlparse(health_url)
    parsed_local = urlparse(local_url)
    if parsed_health.path:
        return urlunparse(
            (
                parsed_local.scheme,
                parsed_local.netloc,
                parsed_health.path,
                "",
                parsed_health.query,
                "",
            )
        )
    return f"{local_url}/api/health"


def progress_text(status: str) -> tuple[str, str]:
    mapping = {
        "ready": ("已接入平台，可打开页面并进行健康检查。", "持续观察运行状态，并补充模块级能力说明。"),
        "integration": ("正在集成，核心链路和服务边界仍在打通。", "完成服务健康检查、部署路由和端到端操作闭环。"),
        "scaffold": ("已建立模块骨架，功能还在规划或初始实现阶段。", "补齐后端接口、前端页面和部署健康检查。"),
        "extension-point": ("作为后续模块接入口，当前用于登记和规划。", "按优先级接入新的实控可视化模块。"),
    }
    return mapping.get(status, ("状态已登记，等待进一步细化。", "补充当前开发进展和下一步计划。"))


async def check_module(module: dict) -> ModuleStatus:
    checked_at = utc_now()
    status = str(module.get("status") or "")
    current_progress = str(module.get("current_progress") or "")
    next_step = str(module.get("next_step") or "")
    default_current, default_next = progress_text(status)
    health_url = module_health_url(module)

    connection_state: Literal["online", "offline", "unknown", "not_configured"] = "not_configured"
    connection_detail = "未配置健康检查地址"
    if health_url:
        connection_state = "unknown"
        connection_detail = "未检查"
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(health_url)
            if 200 <= response.status_code < 400:
                connection_state = "online"
                connection_detail = f"健康检查正常：HTTP {response.status_code}"
            else:
                connection_state = "offline"
                connection_detail = f"健康检查异常：HTTP {response.status_code}"
        except httpx.HTTPError as exc:
            connection_state = "offline"
            connection_detail = f"健康检查失败：{exc}"

    return ModuleStatus(
        id=str(module.get("id") or ""),
        name=str(module.get("name") or ""),
        summary=str(module.get("summary") or ""),
        public_url=str(module.get("public_url") or ""),
        local_url=str(module.get("local_url") or ""),
        service_url=str(module.get("service_url") or ""),
        health_url=str(module.get("health_url") or ""),
        image=str(module.get("image") or ""),
        status=status,
        connection_state=connection_state,
        connection_detail=connection_detail,
        current_progress=current_progress or default_current,
        next_step=next_step or default_next,
        capabilities=list(module.get("capabilities") or []),
        checked_at=checked_at,
    )


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
    return {
        "status": "ok",
        "service": "web-manager",
        "providers": len(load_providers()),
        "modules": len(load_registry()),
    }


@app.get("/api/modules", response_model=list[ModuleStatus])
async def list_modules() -> list[ModuleStatus]:
    return [await check_module(module) for module in load_registry()]


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
