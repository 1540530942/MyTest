# Hermes LLM Gateway

The paper module now deploys a dedicated Hermes sidecar container:

```text
paper-learning-system  -> paper business API and UI
paper-hermes           -> adaptive LLM provider router
```

The paper app calls:

```text
HERMES_URL=http://paper-hermes:8091
```

Hermes then routes each task to the first working provider that has a configured API key.

## Supported Tasks

```text
paper-mining      expand arXiv discovery queries
paper-analysis    generate structured paper interpretation
paper-qa          answer questions about saved papers
practice          generate active-recall Q&A
general           OpenAI-compatible fallback route
```

## Supported Provider Environment Variables

All providers use OpenAI-compatible `/chat/completions` APIs.

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL

DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL

DASHSCOPE_API_KEY
DASHSCOPE_BASE_URL
DASHSCOPE_MODEL

MOONSHOT_API_KEY
MOONSHOT_BASE_URL
MOONSHOT_MODEL

GLM_API_KEY
GLM_BASE_URL
GLM_MODEL

SILICONFLOW_API_KEY
SILICONFLOW_BASE_URL
SILICONFLOW_MODEL

OPENROUTER_API_KEY
OPENROUTER_BASE_URL
OPENROUTER_MODEL
```

Do not commit real API keys. Put them only in `.env`, `.env.cloud`, or server-side secret management.

## Routing Controls

Default task routes are built into `hermes_gateway/main.py`.

Override global provider priority:

```text
HERMES_PROVIDER_ORDER=qwen,deepseek,openai
```

Override task-specific routes with JSON:

```json
{
  "paper-mining": ["deepseek", "glm", "qwen"],
  "paper-analysis": ["deepseek", "glm", "openai"],
  "paper-qa": ["glm", "deepseek"],
  "practice": ["glm", "deepseek"]
}
```

Set that JSON as:

```text
HERMES_TASK_ROUTES=<single-line-json>
```

## Hermes APIs

Health:

```http
GET /api/health
```

Provider status without exposing keys:

```http
GET /api/providers
```

Structured JSON task call:

```http
POST /api/chat-json
```

Body:

```json
{
  "task": "paper-analysis",
  "system": "Return strict JSON...",
  "user": "Title and abstract..."
}
```

OpenAI-compatible proxy:

```http
POST /v1/chat/completions
```

Streaming is intentionally not proxied yet.

## Fallback Behavior

If no provider key is configured, Hermes returns a clear 503. The paper app catches that and uses deterministic local fallback for analysis, Q&A, and practice.

This keeps the deployment runnable without mock data while still using real third-party model calls whenever keys are configured.

## Cloud Deployment Shape

For the platform bundle, the M1 paper module includes:

```text
paper-hermes:local
paper-learning-system:local
```

Only Caddy should be public. Do not expose `8091` to the internet.
