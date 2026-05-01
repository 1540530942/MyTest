# Online Paper Learning System

An independent online paper study system for mining related papers, generating structured paper analyses, and practicing with paper-specific questions and answers.

## Modules

```text
Paper Mining
  -> search arXiv by seed title, abstract, keywords, or arXiv ID
  -> use Hermes to expand discovery queries when model provider keys are configured
  -> save interesting papers to the local library
  -> use curated research_notes links as a dated reference pack

Paper Analysis
  -> generate structured interpretation
  -> summarize background, method, contributions, limitations, and follow-up ideas

Paper Q&A
  -> ask questions about saved papers
  -> auto-generate questions and answers for active recall
  -> reopen saved Q&A as collapsible study-pack items
```

The system is self-contained:

```text
FastAPI backend
  -> Hermes LLM gateway sidecar
  -> SQLite database
  -> Static HTML/CSS/JS study-pack workspace
  -> Docker Compose deployment
```

LLM support is optional. If no Hermes provider key is set, the system uses deterministic local fallback generation so the app can still run offline after papers are added.

## Quick Start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

```text
http://127.0.0.1:8088
```

Health check:

```text
http://127.0.0.1:8088/api/health
```

If Docker cannot pull `python:3.12-slim` from Docker Hub, the project can still run directly with Python for local development. On the cloud server, rerun the Docker build after registry access is available.

If the server has a reachable compatible mirror image, set `PYTHON_IMAGE` in `.env` before building:

```text
PYTHON_IMAGE=python:3.12-slim
```

Keep the image compatible with Python 3.12 slim Debian userspace unless you also adjust the Dockerfile.

## Local Python Run

```powershell
python -m pip install -r requirements.txt
$env:APP_DATABASE="data\papers.db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8088
```

## Configuration

```text
OPENAI_API_KEY      optional LLM key
OPENAI_BASE_URL     OpenAI-compatible base URL
OPENAI_MODEL        model name
HERMES_URL          internal Hermes gateway URL
HERMES_PROVIDER_ORDER optional provider priority
DEEPSEEK_API_KEY    optional DeepSeek-compatible key
DASHSCOPE_API_KEY   optional Qwen/DashScope-compatible key
GLM_API_KEY         optional GLM/Zhipu-compatible key
MOONSHOT_API_KEY    optional Moonshot-compatible key
SILICONFLOW_API_KEY optional SiliconFlow-compatible key
OPENROUTER_API_KEY  optional OpenRouter-compatible key
APP_DATABASE        SQLite database path
API_TOKEN           required for public deployment
```

## Cloud Goal

The final target is deployment on a personal domain and Tencent Cloud server:

```text
https://papers.example.com
  -> Caddy HTTPS reverse proxy
  -> paper-learning FastAPI container
  -> SQLite volume
```

Before public deployment, set a strong `API_TOKEN`, restrict CORS if needed, enable HTTPS, configure backups, and complete ICP/Public Security filing if using a Mainland China Tencent Cloud server.

See:

```text
docs/cloud-deployment-checklist.md
docs/docker-image-deployment.md
docs/hermes-llm-gateway.md
```
