# Multi-Module Control Platform

统一多模块系统入口，用一个域名承载多个独立容器模块。

目标不是把所有业务塞进一个应用，而是形成：

```text
https://control.wangyutang.com
  -> platform gateway / portal
  -> papers.wangyutang.com   paper-learning-system container
  -> remote.wangyutang.com   remote-control container group
  -> sensing.wangyutang.com  remote-sensing container group
  -> camera.wangyutang.cn    TurboPi camera snapshot module
  -> registered future visual-control systems
```

## Module Principles

```text
One module = one or more independent containers
Each module owns its API, data, workers, and device adapters
The platform only handles discovery, navigation, auth boundary, routing, and health aggregation
Modules expose /api/health
Modules are addressed through a stable public route, preferably a subdomain
```

## Initial Modules

| Module | Route | Container responsibility | Status |
| --- | --- | --- | --- |
| Paper Learning | `papers.wangyutang.com` | paper mining, Hermes LLM routing, paper analysis, Q&A, notes | built image ready |
| Remote Control | `remote.wangyutang.com` | web control, FastAPI command API, MQTT, edge bridge | local chain verified |
| Remote Sensing | `sensing.wangyutang.com` | map/sensor imagery ingestion, timeline, visualization | scaffold |
| Camera Snapshot | `camera.wangyutang.cn` | TurboPi/Raspberry Pi camera single-frame and continuous snapshot upload | local module ready |
| Future Systems | registry-driven | more real-control visualization modules | extension point |

## Directory

```text
app/                    platform portal service
modules/registry.json   module catalog consumed by the portal
infra/                  compose and reverse proxy templates
docs/                   architecture and deployment docs
```

## Platform APIs

```text
GET /api/health          platform health
GET /api/modules         module registry
GET /api/modules/health  real module health probes with local-dev fallback
```

## Local Run

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8098
```

Open:

```text
http://127.0.0.1:8098
```

## Docker

```powershell
docker compose up -d --build
```

Build the platform image and package the M1 platform bundle:

```powershell
docker compose build
powershell -ExecutionPolicy Bypass -File scripts\package_platform_bundle.ps1
```

The M1 bundle contains:

```text
control-platform_local.tar
paper-learning-system_local.tar
paper-hermes_local.tar
SHA256SUMS.txt
infra/docker-compose.platform.yml
infra/caddy/Caddyfile
modules registry
roadmap docs
```

## Cloud Shape

Recommended public domains:

```text
papers.wangyutang.com     current paper system
control.wangyutang.com    future unified platform
remote.wangyutang.com     remote control system
sensing.wangyutang.com    remote sensing system
camera.wangyutang.cn      TurboPi camera snapshots
```

If only one public domain is desired later, use path routing only for modules that explicitly support a base path:

```text
https://control.wangyutang.com/papers/
https://control.wangyutang.com/remote/
https://control.wangyutang.com/sensing/
```

## Add A Module

1. Build the module as an independent Docker image.
2. Expose a health endpoint.
3. Add a record to `modules/registry.json`.
4. Add service and reverse-proxy route to Compose/Caddy.
5. Validate from platform `/api/modules`.

See:

```text
docs/optimal-plan-roadmap.md
docs/architecture.md
docs/module-template.md
```
