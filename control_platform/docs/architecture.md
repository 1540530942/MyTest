# Multi-Module Architecture

## Final Direction

Use a subdomain-first multi-container platform.

```text
control.wangyutang.com   platform portal, module catalog, health overview
papers.wangyutang.com    paper learning module
remote.wangyutang.com    remote control module
sensing.wangyutang.com   remote sensing module
camera.wangyutang.cn     TurboPi camera snapshot module
```

Path routing such as `/papers/` is reserved for modules that explicitly support a base path. The current paper system uses root-relative `/static` and `/api` paths, so it should keep its own subdomain.

## Core Principle

```text
The platform is not a mega app.
The platform is a gateway, registry, status board, and policy boundary.
Each business system stays an independent Docker image or container group.
```

## Runtime Shape

```text
Browser
  -> DNS subdomain
  -> Caddy HTTPS reverse proxy
  -> target module container group
  -> module data / device / worker
```

The platform portal talks to the module registry:

```text
control-platform
  -> modules/registry.json
  -> /api/modules
  -> /api/modules/health
  -> web module cards
```

## Why This Is The Best Current Plan

```text
Paper learning is already a working independent image.
Remote control has real hardware and MQTT boundaries; it must split cloud control from edge execution.
Remote sensing may require heavy imagery storage and workers; it must not be coupled to the platform portal.
The Tencent Cloud server is small but enough for portal + paper + lightweight control services.
Subdomains avoid asset-path conflicts and make future module replacement simpler.
```

## Module Container Groups

### Platform

```text
control-platform
  -> module registry
  -> navigation
  -> health/status overview
  -> roadmap and docs entry
```

### Paper Learning

```text
paper-learning-system
  -> FastAPI
  -> static study-pack UI
  -> SQLite volume
  -> arXiv mining

paper-hermes
  -> adaptive OpenAI-compatible provider router
  -> task routes for mining, analysis, Q&A, and practice
  -> provider fallback across OpenAI, DeepSeek, Qwen/DashScope, Moonshot, SiliconFlow, OpenRouter, or custom JSON providers
```

Current image:

```text
paper-learning-system:local
```

### Remote Control

Recommended split:

```text
remote-control-web
remote-control-api
remote-control-mqtt
remote-control-edge-bridge
```

Important boundary:

```text
Cloud server cannot directly access a USB COM port on the local Windows PC.
Serial bridge belongs on the edge device or local PC.
Cloud should publish commands to MQTT and receive state back.
```

Production target:

```text
Cloud API/MQTT
  -> ESP32 or edge gateway
  -> real device action
  -> state and audit feedback
```

### Remote Sensing

Recommended split:

```text
remote-sensing-ui
remote-sensing-api
remote-sensing-worker
remote-sensing-store
```

Start small:

```text
metadata catalog
map layer registry
timeline playback
region-of-interest records
alert events
```

Defer heavy GeoTIFF processing and tile generation until the base module works.

### Camera Snapshot

```text
camera-snapshot
  -> FastAPI
  -> static camera control UI
  -> latest JPEG storage volume
  -> task polling API for Raspberry Pi sender
```

Boundary:

```text
Cloud server does not dial into the robot.
TurboPi / Raspberry Pi runs pi_camera_sender.py and makes outbound HTTPS requests.
The browser creates single-frame or continuous-upload tasks.
```

## Security Model

Phase 1:

```text
Caddy HTTPS
per-module API_TOKEN
private Docker network
no public 8088 / 1883 / database ports
```

Phase 2:

```text
shared auth boundary
module-level roles
audit logs for all real-control actions
command signing or short-lived tokens for edge devices
```

For physical control modules, use a safer command lifecycle:

```text
draft command
validate command
arm command
execute command
record result
publish state
```

## Module Contract

Every module record should provide:

```text
id
name
public_url
local_url
route_strategy
path_prefix
service_url
health_url
image
status
summary
capabilities
data_owner
```

The registry lives at:

```text
modules/registry.json
```
