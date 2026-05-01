# LLM Manager 模块记录

新增路径：`wangyutang_platform/llm_manager`

## 作用

`llm_manager` 是平台里的大模型接口管理模块。它独立运行在 `llm-manager:8092`，用于统一保存 OpenAI-compatible API 配置，并给后续其他模块提供共享的大模型对话接口。

## 路由

```text
本地服务：http://127.0.0.1:8092/
平台路由：http://www.wangyutang.cn/llm/
健康检查：http://127.0.0.1:8092/api/health
共享调用：http://127.0.0.1:8092/api/chat
```

## API

```text
GET    /api/providers
POST   /api/providers
DELETE /api/providers/{provider_id}
POST   /api/chat
```

`/api/chat` 接收 OpenAI Chat Completions 风格的 `messages`，由配置好的 provider 转发到对应模型服务。

## 配置保存

Provider 配置保存在 Docker 数据卷 `llm_manager_data` 中。API Key 可以直接保存在配置里，也可以通过 `api_key_env` 指向容器环境变量，例如 `OPENAI_API_KEY`。

## 已接入文件

```text
docker-compose.yml
.env
.env.example
control_platform/infra/caddy/Caddyfile
control_platform/modules/registry.json
scripts/check-local.ps1
README.md
```
