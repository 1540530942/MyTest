from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


DEFAULT_TASK_ROUTES = {
    "paper-mining": ["deepseek", "glm", "qwen", "openai", "moonshot", "siliconflow", "openrouter"],
    "paper-analysis": ["deepseek", "glm", "openai", "qwen", "moonshot", "siliconflow", "openrouter"],
    "paper-qa": ["glm", "deepseek", "qwen", "openai", "moonshot", "siliconflow", "openrouter"],
    "practice": ["glm", "deepseek", "qwen", "openai", "moonshot", "siliconflow", "openrouter"],
    "general": ["deepseek", "glm", "openai", "qwen", "moonshot", "siliconflow", "openrouter"],
}

PROVIDER_DEFAULTS = {
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_BASE_URL",
        "base_url": "https://api.openai.com/v1",
        "model_env": "OPENAI_MODEL",
        "model": "gpt-4.1-mini",
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "base_url": "https://api.deepseek.com",
        "model_env": "DEEPSEEK_MODEL",
        "model": "deepseek-chat",
    },
    "qwen": {
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url_env": "DASHSCOPE_BASE_URL",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_env": "DASHSCOPE_MODEL",
        "model": "qwen-plus",
    },
    "glm": {
        "api_key_env": "GLM_API_KEY",
        "base_url_env": "GLM_BASE_URL",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model_env": "GLM_MODEL",
        "model": "glm-4-flash",
    },
    "moonshot": {
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url_env": "MOONSHOT_BASE_URL",
        "base_url": "https://api.moonshot.cn/v1",
        "model_env": "MOONSHOT_MODEL",
        "model": "moonshot-v1-8k",
    },
    "siliconflow": {
        "api_key_env": "SILICONFLOW_API_KEY",
        "base_url_env": "SILICONFLOW_BASE_URL",
        "base_url": "https://api.siliconflow.cn/v1",
        "model_env": "SILICONFLOW_MODEL",
        "model": "Qwen/Qwen2.5-72B-Instruct",
    },
    "openrouter": {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url": "https://openrouter.ai/api/v1",
        "model_env": "OPENROUTER_MODEL",
        "model": "openai/gpt-4o-mini",
    },
}


@dataclass(frozen=True)
class Provider:
    name: str
    api_key: str
    base_url: str
    model: str


class ChatJsonRequest(BaseModel):
    system: str = Field(min_length=1)
    user: str = Field(min_length=1)
    task: str = "general"
    provider: str = ""
    model: str = ""
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32000)


class OpenAIChatRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]]
    temperature: float | None = 0.2
    max_tokens: int | None = None
    response_format: dict[str, Any] | None = None
    stream: bool | None = False


app = FastAPI(title="Paper Hermes LLM Gateway")


def require_token(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("HERMES_API_TOKEN", "").strip()
    if not token:
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Missing or invalid Hermes token")


def load_custom_providers() -> dict[str, Provider]:
    raw = os.getenv("HERMES_PROVIDERS_JSON", "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("HERMES_PROVIDERS_JSON is not valid JSON") from exc

    providers: dict[str, Provider] = {}
    for item in data:
        name = str(item.get("name", "")).strip()
        api_key = str(item.get("api_key", "")).strip()
        base_url = str(item.get("base_url", "")).strip().rstrip("/")
        model = str(item.get("model", "")).strip()
        if name and api_key and base_url and model:
            providers[name] = Provider(name=name, api_key=api_key, base_url=base_url, model=model)
    return providers


def load_providers() -> dict[str, Provider]:
    providers: dict[str, Provider] = {}
    for name, config in PROVIDER_DEFAULTS.items():
        api_key = os.getenv(config["api_key_env"], "").strip()
        if not api_key:
            continue
        base_url = os.getenv(config["base_url_env"], config["base_url"]).strip().rstrip("/")
        model = os.getenv(config["model_env"], config["model"]).strip()
        providers[name] = Provider(name=name, api_key=api_key, base_url=base_url, model=model)

    providers.update(load_custom_providers())
    return providers


def task_routes() -> dict[str, list[str]]:
    raw = os.getenv("HERMES_TASK_ROUTES", "").strip()
    if not raw:
        return DEFAULT_TASK_ROUTES
    data = json.loads(raw)
    routes = dict(DEFAULT_TASK_ROUTES)
    for task, providers in data.items():
        if isinstance(providers, list):
            routes[str(task)] = [str(provider) for provider in providers]
    return routes


def provider_order(requested_provider: str, task: str, providers: dict[str, Provider]) -> list[Provider]:
    if requested_provider:
        provider = providers.get(requested_provider)
        return [provider] if provider else []

    explicit_order = [item.strip() for item in os.getenv("HERMES_PROVIDER_ORDER", "").split(",") if item.strip()]
    route_names = explicit_order or task_routes().get(task) or task_routes()["general"]
    ordered = [providers[name] for name in route_names if name in providers]
    remaining = [provider for name, provider in providers.items() if name not in route_names]
    return ordered + remaining


def parse_json_content(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(content[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("model response is not a JSON object")
    return parsed


def build_headers(provider: Provider) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }
    if provider.name == "openrouter":
        referer = os.getenv("OPENROUTER_SITE_URL", "").strip()
        title = os.getenv("OPENROUTER_APP_TITLE", "Paper Learning System").strip()
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
    return headers


async def post_chat_completion(provider: Provider, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{provider.base_url}/chat/completions",
            json=payload,
            headers=build_headers(provider),
        )
        response.raise_for_status()
        return response.json()


async def call_provider_json(
    provider: Provider,
    request: ChatJsonRequest,
    timeout: float,
) -> tuple[dict[str, Any], bool]:
    model = request.model or provider.model
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": request.system},
            {"role": "user", "content": request.user},
        ],
        "temperature": request.temperature,
        "response_format": {"type": "json_object"},
    }
    if request.max_tokens:
        payload["max_tokens"] = request.max_tokens

    try:
        data = await post_chat_completion(provider, payload, timeout)
        return data, True
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code not in {400, 422}:
            raise

    payload.pop("response_format", None)
    payload["messages"][0]["content"] = (
        request.system.rstrip()
        + "\nReturn only one valid JSON object. Do not include Markdown fences."
    )
    data = await post_chat_completion(provider, payload, timeout)
    return data, False


async def call_provider_raw(
    provider: Provider,
    request: OpenAIChatRequest,
    timeout: float,
) -> dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload["model"] = request.model or provider.model
    payload["stream"] = False
    return await post_chat_completion(provider, payload, timeout)


@app.get("/api/health")
def health() -> dict[str, Any]:
    providers = load_providers()
    return {
        "ok": "true",
        "enabled_providers": sorted(providers),
        "provider_count": len(providers),
    }


@app.get("/api/providers", dependencies=[Depends(require_token)])
def providers() -> dict[str, Any]:
    enabled = load_providers()
    configured = []
    for name, config in PROVIDER_DEFAULTS.items():
        provider = enabled.get(name)
        configured.append(
            {
                "name": name,
                "enabled": provider is not None,
                "api_key_env": config["api_key_env"],
                "base_url": provider.base_url if provider else os.getenv(config["base_url_env"], config["base_url"]),
                "model": provider.model if provider else os.getenv(config["model_env"], config["model"]),
            }
        )
    for name, provider in enabled.items():
        if name not in PROVIDER_DEFAULTS:
            configured.append(
                {
                    "name": name,
                    "enabled": True,
                    "api_key_env": "HERMES_PROVIDERS_JSON",
                    "base_url": provider.base_url,
                    "model": provider.model,
                }
            )
    return {"providers": configured, "task_routes": task_routes()}


@app.post("/api/chat-json", dependencies=[Depends(require_token)])
async def chat_json(request: ChatJsonRequest) -> dict[str, Any]:
    providers = load_providers()
    ordered = provider_order(request.provider, request.task, providers)
    if not ordered:
        raise HTTPException(status_code=503, detail="No Hermes provider is enabled for this task")

    timeout = float(os.getenv("HERMES_HTTP_TIMEOUT_SECONDS", os.getenv("HTTP_TIMEOUT_SECONDS", "45")))
    attempts = []
    for provider in ordered:
        started = time.perf_counter()
        try:
            data, used_json_mode = await call_provider_json(provider, request, timeout)
            content = data["choices"][0]["message"]["content"]
            result = parse_json_content(content)
            attempts.append(
                {
                    "provider": provider.name,
                    "model": request.model or provider.model,
                    "ok": True,
                    "json_mode": used_json_mode,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000),
                }
            )
            return {
                "ok": True,
                "task": request.task,
                "provider": provider.name,
                "model": request.model or provider.model,
                "result": result,
                "attempts": attempts,
            }
        except Exception as exc:
            attempts.append(
                {
                    "provider": provider.name,
                    "model": request.model or provider.model,
                    "ok": False,
                    "error": exc.__class__.__name__,
                    "detail": str(exc)[:500],
                    "elapsed_ms": round((time.perf_counter() - started) * 1000),
                }
            )

    raise HTTPException(status_code=502, detail={"message": "All Hermes providers failed", "attempts": attempts})


@app.post("/v1/chat/completions", dependencies=[Depends(require_token)])
async def openai_compatible_chat(request: OpenAIChatRequest) -> dict[str, Any]:
    if request.stream:
        raise HTTPException(status_code=400, detail="Hermes gateway does not proxy streaming responses yet")

    providers = load_providers()
    ordered = provider_order("", "general", providers)
    if not ordered:
        raise HTTPException(status_code=503, detail="No Hermes provider is enabled")

    timeout = float(os.getenv("HERMES_HTTP_TIMEOUT_SECONDS", os.getenv("HTTP_TIMEOUT_SECONDS", "45")))
    errors = []
    for provider in ordered:
        try:
            return await call_provider_raw(provider, request, timeout)
        except Exception as exc:
            errors.append({"provider": provider.name, "error": exc.__class__.__name__, "detail": str(exc)[:500]})

    raise HTTPException(status_code=502, detail={"message": "All Hermes providers failed", "attempts": errors})
