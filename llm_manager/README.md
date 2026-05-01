# LLM Manager

大模型接口管理模块，负责保存 OpenAI-compatible API 配置，并给其他模块提供统一的对话调用入口。

## HTTP API

```text
GET  /api/health
GET  /api/providers
POST /api/providers
DELETE /api/providers/{provider_id}
POST /api/chat
```

`POST /api/chat` 使用 OpenAI Chat Completions 兼容格式：

```json
{
  "provider_id": "openai",
  "model": "gpt-4.1-mini",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
```

Provider 的 API Key 可以直接保存在模块数据卷里，也可以只配置 `api_key_env`，让容器从环境变量读取，例如 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY`。

## Local

```powershell
docker compose up --build llm-manager
```

本地访问：

```text
http://127.0.0.1:8092/
```
