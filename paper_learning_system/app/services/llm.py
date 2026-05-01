from __future__ import annotations

import os
from typing import Any

import httpx


def llm_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


async def chat_json(
    system: str,
    user: str,
    task: str = "general",
    provider: str = "",
    model: str = "",
) -> dict[str, Any] | None:
    hermes_url = os.getenv("HERMES_URL", "").strip().rstrip("/")
    if hermes_url:
        return await chat_json_via_hermes(hermes_url, system, user, task, provider=provider, model=model)

    return await chat_json_direct(system, user)


async def chat_json_via_hermes(
    hermes_url: str,
    system: str,
    user: str,
    task: str,
    provider: str = "",
    model: str = "",
) -> dict[str, Any] | None:
    timeout = float(os.getenv("HERMES_HTTP_TIMEOUT_SECONDS", os.getenv("HTTP_TIMEOUT_SECONDS", "45")))
    payload = {
        "system": system,
        "user": user,
        "task": task,
        "provider": provider,
        "model": model,
        "temperature": float(os.getenv("HERMES_TEMPERATURE", "0.2")),
    }
    headers = {"Content-Type": "application/json"}
    token = os.getenv("HERMES_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{hermes_url}/api/chat-json", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return None

    result = data.get("result")
    if not isinstance(result, dict):
        return None

    result.setdefault(
        "_hermes",
        {
            "provider": data.get("provider", ""),
            "model": data.get("model", ""),
            "task": data.get("task", task),
        },
    )
    return result


async def chat_json_direct(system: str, user: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    import json

    content = data["choices"][0]["message"]["content"]
    return json.loads(content)
