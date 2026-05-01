# Optimal Plan And Roadmap

## Review Snapshot

Reviewed on 2026-04-16.

Current local artifacts:

```text
control-platform:local        built, amd64, healthy on http://127.0.0.1:8098
paper-learning-system:local   built, amd64, healthy on http://127.0.0.1:8088
paper-hermes:local            built, amd64, healthy on http://127.0.0.1:8091 in smoke test
module health aggregation     implemented at /api/modules/health
```

Current M1 cloud bundle:

```text
C:\Users\Administrator\Desktop\Workspace\Project_Codex\Arduino_interact\git_workspace\control_platform\dist\platform_bundle
```

Bundle checksums:

```text
4E4305CA5EAADBEECEE5BEF3090073DEC4BA0B9212D69F740AAD7F2233031847  control-platform_local.tar
C4538E554E84A35A151E10BA9A30AF04B6EC545B48EF2D7DA3EA2505EDD6B1B1  paper-hermes_local.tar
86BC683DB83B32CC8D5B18F8DA280759A086361D7FBEDA7AD0B90F7CA078E7A1  paper-learning-system_local.tar
```

## Executive Decision

Build a subdomain-first, container-per-module control platform.

```text
control.wangyutang.com   unified platform portal
papers.wangyutang.com    module 1: paper learning
remote.wangyutang.com    module 2: remote control
sensing.wangyutang.com   module 3: remote sensing
camera.wangyutang.cn     module 4: TurboPi camera snapshots
```

The platform should not own module internals. It should own:

```text
module registry
navigation
health aggregation
deployment documentation
future auth/audit policy
```

## Current Implementation Review

### Paper Learning System

Status:

```text
ready
Docker image built
health checked
reference-paper pack integrated
cloud bundle generated
Hermes LLM gateway sidecar added for adaptive third-party model routing
```

Assessment:

```text
Good first module.
Keep it on papers.wangyutang.com because the frontend currently assumes root paths like /static and /api.
Do not force it under control.wangyutang.com/papers/ until it supports a base path.
```

### Remote Control System

Status:

```text
local real chain verified
cloud containerization not complete
hardware boundary exists
```

Assessment:

```text
Split cloud and edge.
The cloud server can host web/API/MQTT.
The PC Serial Bridge or Arduino USB bridge must run where the hardware is physically connected.
For a true cloud product, move the edge side to ESP32 or a local gateway.
```

### Remote Sensing System

Status:

```text
concept/scaffold
```

Assessment:

```text
Start as metadata + map/timeline visualization.
Avoid heavy imagery processing on the 4-core/4GB/3Mbps server at first.
Add workers and external object storage later if real imagery volume grows.
```

### Control Platform

Status:

```text
scaffold built
module registry working
local portal running on 8098
compose config checked
```

Assessment:

```text
Good as a portal and registry.
Needs health aggregation, auth boundary, and deployment packaging next.
```

## Roadmap

### M0: Architecture Freeze

Status:

```text
complete locally
```

Deliverables:

```text
subdomain-first routing decision
module registry schema
module contract
roadmap documents
DNS plan for control/papers/remote/sensing
```

Acceptance:

```text
docs explain why subdomains are preferred
registry records include public_url and route_strategy
platform local page lists all modules
platform probes module health without mock status
```

### M1: Deploy Platform + Paper Module

Status:

```text
local build complete
combined cloud bundle complete
waiting for DNS/firewall/upload/server deployment
```

Deliverables:

```text
control-platform Docker image
paper-learning-system Docker image
paper-hermes Docker image
combined cloud bundle
Caddy routes for control.wangyutang.com and papers.wangyutang.com
server .env.platform
Hermes provider-key and routing configuration
```

Acceptance:

```text
https://control.wangyutang.com opens module portal
https://papers.wangyutang.com opens paper system
both containers are healthy
paper module can import reference pack and generate Q&A
Hermes can route to configured third-party providers
8088 and 8098 are private behind Caddy
8091 is private inside Docker network
```

### M2: Remote Control Cloud Module

Status:

```text
next implementation phase
local real chain exists, production cloud split still required
```

Deliverables:

```text
remote-control-api Docker image
remote-control-web Docker image
Mosquitto or EMQX container
edge bridge connection plan
MQTT topic contract
command audit table/log
```

Acceptance:

```text
https://remote.wangyutang.com opens remote dashboard
API publishes validated command to MQTT
edge bridge receives command and publishes state
dangerous commands require validation and audit
```

### M3: Remote Sensing MVP

Status:

```text
planned after remote-control cloud boundary is defined
```

Deliverables:

```text
remote-sensing-api Docker image
remote-sensing-ui Docker image
metadata catalog
map/timeline UI
sample layer import
alert-event model
```

Acceptance:

```text
https://sensing.wangyutang.com opens sensing dashboard
sample sensing records can be listed
map/timeline view works
health endpoint works
```

### M4: Platform Operations

Status:

```text
hardening phase after M1 cloud deployment
```

Deliverables:

```text
module status polling
container status docs
backup scripts
restore procedure
runtime log strategy
```

Acceptance:

```text
control portal shows module health
SQLite backup and restore are tested
paper module survives container restart
```

### M5: Shared Auth And Real-Control Safety

Status:

```text
required before broad public real-control access
```

Deliverables:

```text
shared login or gateway token policy
module-level role matrix
audit logs
real-control command lifecycle
edge-device credential rotation
```

Acceptance:

```text
unauthenticated users cannot issue commands
all real-control actions are auditable
operator can distinguish preview/draft/execute states
```

### M6: Plugin-Style Expansion

Status:

```text
after at least three modules have stable contracts
```

Deliverables:

```text
module onboarding template
image naming policy
route allocation policy
sample fourth module
versioned registry
```

Acceptance:

```text
new module can be added by image + registry + Caddy route
platform displays it without code changes
```

## DNS Roadmap

Create these Spaceship records:

```text
papers   A  110.40.154.41
control  A  110.40.154.41
remote   A  110.40.154.41
sensing  A  110.40.154.41
camera   A  110.40.154.41
```

Minimum for M1:

```text
papers
control
```

## What Not To Do

```text
Do not merge all systems into one container.
Do not expose module internal ports publicly.
Do not put USB serial bridge only on the cloud server.
Do not make remote sensing heavy processing part of the portal.
Do not rely on /papers/ path routing until paper system supports base path.
```
