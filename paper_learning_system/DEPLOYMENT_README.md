# Multi-Module Platform Deployment README

This document records the current best deployment plan after purchasing the domain and Tencent Cloud server.

The plan has changed from a single paper-learning site to a scalable multi-module platform. The paper-learning system remains the first ready module.

## Confirmed Information

```text
Domain registrar: Spaceship
Root domain: wangyutang.com

Tencent Cloud product: Lighthouse
Instance ID: lhins-cfcgqi2u
Instance name: OpenCloudOS-j1XW
Region: ap-shanghai
Public IP: 110.40.154.41
Operating system: OpenCloudOS 9
Default SSH username: root
CPU / memory: 4 cores / 4 GB
System disk: 40 GB SSD
Bandwidth: 3 Mbps
Monthly traffic package: 300 GB
```

The server password was provided for this session, but it is not stored in this project.

## Optimal Architecture

Use a subdomain-first, container-per-module platform.

```text
control.wangyutang.com   unified platform portal
papers.wangyutang.com    module 1: paper learning system
remote.wangyutang.com    module 2: remote control system
sensing.wangyutang.com   module 3: remote sensing system
camera.wangyutang.cn     module 4: TurboPi camera snapshot system
```

The platform should not merge all business systems into one application. It should own:

```text
module registry
navigation
health/status overview
deployment documentation
future shared auth and audit boundary
```

Each module should own its own:

```text
Docker image or container group
API
UI
data volume
workers
device or data adapters
health endpoint
```

Path routing such as `control.wangyutang.com/papers/` is reserved for future modules that explicitly support a base path. The current paper system should stay on `papers.wangyutang.com` because it uses root-relative `/api` and `/static` paths.

## Current Local Build Status

### Platform Portal

```text
Project path: C:\Users\Administrator\Desktop\Workspace\Project_Codex\Arduino_interact\git_workspace\control_platform
Docker image: control-platform:local
Image architecture: linux/amd64
Local URL: http://127.0.0.1:8098
Health endpoint: http://127.0.0.1:8098/api/health
Status: healthy after restart
```

### Paper Learning Module

```text
Project path: C:\Users\Administrator\Desktop\Workspace\Project_Codex\Arduino_interact\git_workspace\paper_learning_system
Docker image: paper-learning-system:local
Image architecture: linux/amd64
Local container: paper-learning-system
Local URL: http://127.0.0.1:8088
Health endpoint: http://127.0.0.1:8088/api/health
Status: healthy
```

## Preferred Cloud Bundle

Use the combined platform bundle for M1 deployment:

```text
C:\Users\Administrator\Desktop\Workspace\Project_Codex\Arduino_interact\git_workspace\control_platform\dist\platform_bundle
```

Important files inside the bundle:

```text
control-platform_local.tar
paper-hermes_local.tar
paper-learning-system_local.tar
SHA256SUMS.txt
README.md
registry.json
docs/architecture.md
docs/module-template.md
docs/optimal-plan-roadmap.md
infra/docker-compose.platform.yml
infra/env.platform.example
infra/caddy/Caddyfile
```

Current image archive checksums:

```text
4E4305CA5EAADBEECEE5BEF3090073DEC4BA0B9212D69F740AAD7F2233031847  control-platform_local.tar
C4538E554E84A35A151E10BA9A30AF04B6EC545B48EF2D7DA3EA2505EDD6B1B1  paper-hermes_local.tar
86BC683DB83B32CC8D5B18F8DA280759A086361D7FBEDA7AD0B90F7CA078E7A1  paper-learning-system_local.tar
```

The standalone paper-module bundle also exists at:

```text
C:\Users\Administrator\Desktop\Workspace\Project_Codex\Arduino_interact\git_workspace\paper_learning_system\dist\cloud_bundle
```

For the new multi-module direction, prefer the combined platform bundle.

## What You Need To Do

### 1. Configure Spaceship DNS

Minimum M1 records:

```text
Type: A
Host: control
Value: 110.40.154.41
TTL: Auto or 300

Type: A
Host: papers
Value: 110.40.154.41
TTL: Auto or 300
```

Optional records can be added now to reserve the next modules:

```text
Type: A
Host: remote
Value: 110.40.154.41
TTL: Auto or 300

Type: A
Host: sensing
Value: 110.40.154.41
TTL: Auto or 300
```

Expected result:

```text
control.wangyutang.com -> 110.40.154.41
papers.wangyutang.com  -> 110.40.154.41
remote.wangyutang.com  -> 110.40.154.41
sensing.wangyutang.com -> 110.40.154.41
```

Do not use `http://` or `https://` in DNS values.

### 2. Configure Tencent Cloud Firewall / Security Group

Allow:

```text
22/tcp
80/tcp
443/tcp
```

Do not expose:

```text
8088/tcp
8098/tcp
1883/tcp unless intentionally exposing MQTT with TLS/auth later
Docker daemon ports
SQLite volume paths
```

Public traffic should enter through Caddy on 80/443.

### 3. Open Tencent Cloud OrcaTerm

Use:

```text
https://orcaterm.cloud.tencent.com/terminal?type=lighthouse&instanceId=lhins-cfcgqi2u&region=ap-shanghai&from=lh_console_login_btn
```

Confirm that you can enter the server terminal as `root`.

### 4. Upload The Platform Bundle

Upload this local folder:

```text
C:\Users\Administrator\Desktop\Workspace\Project_Codex\Arduino_interact\git_workspace\control_platform\dist\platform_bundle
```

Recommended server path:

```text
/root/control_platform
```

After upload, the server should have:

```text
/root/control_platform/control-platform_local.tar
/root/control_platform/paper-hermes_local.tar
/root/control_platform/paper-learning-system_local.tar
/root/control_platform/infra/docker-compose.platform.yml
/root/control_platform/infra/env.platform.example
/root/control_platform/infra/caddy/Caddyfile
```

### 5. Tell Codex When Ready

After DNS, firewall, OrcaTerm access, and upload are done, tell Codex:

```text
DNS added, ports opened, platform_bundle uploaded to /root/control_platform.
```

## What Codex Will Do Next

### 1. Verify DNS And Ports

Codex will check:

```text
control.wangyutang.com resolves to 110.40.154.41
papers.wangyutang.com resolves to 110.40.154.41
110.40.154.41:22 is reachable
110.40.154.41:80 is reachable after deployment
110.40.154.41:443 is reachable after deployment
```

### 2. Prepare OpenCloudOS 9

Codex will install or enable Docker and Docker Compose support on the server if needed.

### 3. Create Production Environment File

Create:

```text
/root/control_platform/infra/.env.platform
```

From:

```text
/root/control_platform/infra/env.platform.example
```

Expected production values:

```text
PLATFORM_DOMAIN=control.wangyutang.com
PAPERS_DOMAIN=papers.wangyutang.com
REMOTE_DOMAIN=remote.wangyutang.com
SENSING_DOMAIN=sensing.wangyutang.com
CAMERA_DOMAIN=camera.wangyutang.cn
CONTROL_PLATFORM_IMAGE=control-platform:local
PAPER_LEARNING_IMAGE=paper-learning-system:local
PAPER_HERMES_IMAGE=paper-hermes:local
CAMERA_SNAPSHOT_IMAGE=camera-snapshot:local
HERMES_URL=http://paper-hermes:8091
HERMES_API_TOKEN=<optional internal token>
HERMES_PROVIDER_ORDER=<optional provider order such as qwen,deepseek,openai>
API_TOKEN=<generated long random token>
OPENAI_API_KEY=<optional>
DEEPSEEK_API_KEY=<optional>
DASHSCOPE_API_KEY=<optional>
MOONSHOT_API_KEY=<optional>
SILICONFLOW_API_KEY=<optional>
OPENROUTER_API_KEY=<optional>
```

The `API_TOKEN` will be generated on the server and should be saved securely.

### 4. Load Docker Images

Run on the server:

```bash
cd /root/control_platform
docker load -i control-platform_local.tar
docker load -i paper-hermes_local.tar
docker load -i paper-learning-system_local.tar
```

Expected images:

```text
control-platform:local
paper-hermes:local
paper-learning-system:local
```

### 5. Start The Platform

Run:

```bash
cd /root/control_platform/infra
docker compose --env-file .env.platform -f docker-compose.platform.yml up -d
docker compose --env-file .env.platform -f docker-compose.platform.yml ps
```

This starts:

```text
control-platform-caddy
control-platform
paper-hermes
paper-learning-system
```

The remote-control and remote-sensing domains are planned routes. They should return a controlled placeholder until their module containers are built.

### 6. Verify The Deployment

Local server checks:

```bash
curl http://127.0.0.1:8098/api/health
curl http://127.0.0.1:8098/api/modules/health
curl http://127.0.0.1:8088/api/health
docker exec paper-hermes python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8091/api/health', timeout=3).read().decode())"
docker ps
docker logs control-platform --tail=100
docker logs paper-hermes --tail=100
docker logs paper-learning-system --tail=100
docker logs control-platform-caddy --tail=100
```

Public checks after DNS and HTTPS are ready:

```bash
curl https://control.wangyutang.com/api/health
curl https://papers.wangyutang.com/api/health
```

Expected health response:

```json
{"ok":"true"}
```

## Roadmap

### M0: Architecture Freeze

Status: complete locally.

```text
Subdomain-first routing chosen
Module registry created
Platform scaffold created
Roadmap and architecture docs written
```

### M1: Deploy Platform + Paper Module

Status: local build complete, cloud deployment pending.

```text
Deploy control.wangyutang.com
Deploy papers.wangyutang.com
Use combined platform bundle
Keep 8088 and 8098 private behind Caddy
```

### M2: Remote Control Cloud Module

Status: integration next.

```text
Split cloud API/MQTT from edge serial bridge
Containerize remote-control web/API/MQTT
Run hardware bridge on the PC or edge gateway that physically connects to Arduino/ESP32
Add audit logs and command validation before real public control
```

### M3: Remote Sensing MVP

Status: scaffold next.

```text
Start with metadata catalog
Add map/timeline visualization
Add sample data import
Defer heavy imagery processing until storage and worker design are ready
```

### M4: Platform Operations

Status: later hardening.

```text
Add health aggregation
Add backup and restore scripts
Add centralized runtime log policy
Add module onboarding template
```

### M5: Shared Auth And Real-Control Safety

Status: required before broad public real-control use.

```text
Shared login or gateway token policy
Module-level roles
Command draft/validate/arm/execute lifecycle
Audit logs for all real device actions
Edge credential rotation
```

## Final Acceptance Criteria For M1

```text
https://control.wangyutang.com opens the module portal
https://papers.wangyutang.com opens the paper learning workspace
HTTPS certificates are valid
control-platform and paper-learning-system containers are healthy
paper-hermes container is healthy
Hermes routes to configured third-party LLM providers when provider keys are set
API rejects protected requests without the correct Bearer token when API_TOKEN is set
Reference paper pack loads
arXiv mining works from the cloud server
paper analysis works with local fallback
paper question answering works
practice questions are generated and saved
SQLite data survives container restart
8088 and 8098 are not publicly exposed
8091 is not publicly exposed
```

## Current Blockers

```text
Spaceship DNS records may not yet be configured or propagated
HTTPS/domain access is pending DNS propagation and certificate issuance
ICP / public security filing decision is needed if this Mainland China server hosts a public website
Remote-control cloud module is not yet containerized for production
Remote-sensing module is not yet implemented
DeepSeek provider key currently returns 401 unauthorized; GLM provider works
Browser or system proxy may need to bypass 110.40.154.41 for direct-IP testing
```

## Latest Cloud Verification

```text
Verified on: 2026-04-19
Direct platform URL: http://110.40.154.41/
Direct paper URL: http://110.40.154.41/papers/
Paper health URL: http://110.40.154.41/papers/api/health

control-platform: healthy
paper-learning-system: healthy
paper-hermes: healthy
control-platform-caddy: running on 80/443

Paper page status: 200
Paper health status: 200 {"ok":"true"}
Paper static app.js status: 200
Hermes chat endpoint status: 200
Hermes active provider: glm
Hermes active model: glm-4-flash
Hermes web chat no longer requires API_TOKEN
Hermes web chat supports provider/model selection from the page
Library management APIs still require API_TOKEN
```
