# Web Manager

Web Manager 是平台里的模块网页监督台。它负责监督各个模块网页和服务的执行状态，包括连接状态、当前开发进展、下一步计划，同时内置大模型接口管理能力。

> 代码目录暂时仍为 `llm_manager`，用于兼容现有构建路径和数据卷；服务身份、页面标题、注册信息已经改为 `web-manager`。

## 功能

- 从 `control_platform/modules/registry.json` 读取平台模块清单。
- 检查各模块健康检查地址，展示在线、离线、未配置等连接状态。
- 汇总模块当前开发进展和下一步计划。
- 管理多个模型 Provider，例如 OpenAI、DeepSeek、自建兼容接口。
- 支持直接保存 API Key，或通过环境变量读取 API Key。
- 提供统一的 `/api/chat` 接口，转发到选定 Provider 的 Chat Completions 接口。

## HTTP API

```text
GET    /api/health
GET    /api/modules
GET    /api/providers
POST   /api/providers
DELETE /api/providers/{provider_id}
POST   /api/chat
```

`GET /api/modules` 返回各模块的注册信息、连接状态、当前进展和下一步计划。

`POST /api/chat` 使用 OpenAI Chat Completions 兼容格式：

```json
{
  "provider_id": "openai",
  "model": "gpt-4.1-mini",
  "messages": [
    { "role": "user", "content": "你好" }
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
```

Provider 的 API Key 可以直接保存在模块数据卷里，也可以只配置 `api_key_env`，让容器从环境变量读取，例如 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY`。

## 本地运行

在平台根目录执行：

```powershell
docker compose up --build web-manager
```

本地访问：

```text
http://127.0.0.1:8092/
```
