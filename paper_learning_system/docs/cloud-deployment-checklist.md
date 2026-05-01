# Cloud Deployment Checklist

This system is designed to become a standalone service on a personal domain and Tencent Cloud server.

## Information Needed

```text
Domain name: wangyutang.com
Domain registrar: Spaceship
Preferred subdomain: papers.wangyutang.com
Tencent Cloud CVM public IP: 110.40.154.41
Instance: OpenCloudOS-j1XW
Operating system: OpenCloudOS 9
CPU / memory: 4 cores / 4 GB
System disk: 40 GB SSD
Bandwidth: 3 Mbps
Monthly traffic package: 300 GB
Server region: ap-shanghai
SSH username: root
SSH password received for this session, not stored in project files
sudo permission
DNS provider access
Security group edit permission
ICP filing status if the server is in Mainland China
OpenAI-compatible LLM provider and API key, if LLM mode is required
Backup location for SQLite data
```

## Tencent Cloud And Domain Notes

For a Mainland China Tencent Cloud CVM, complete ICP filing before public access. After the site opens, complete Public Security Network Filing within the required window and display filing numbers in the site footer.

For Hong Kong or overseas CVM regions, the launch path is simpler, but latency and compliance requirements should still be reviewed.

Tencent Cloud links:

```text
Lighthouse console:
https://console.cloud.tencent.com/lighthouse/instance/index?rid=1

OrcaTerm web terminal:
https://orcaterm.cloud.tencent.com/terminal?type=lighthouse&instanceId=lhins-cfcgqi2u&region=ap-shanghai&from=lh_console_login_btn
```

## DNS

Domain registrar currently recorded:

```text
Spaceship
```

Create:

```text
papers.wangyutang.com A -> 110.40.154.41
```

On Spaceship DNS, add an `A` record:

```text
Type: A
Host: papers
Value: 110.40.154.41
TTL: automatic or 300 seconds
```

If using the root domain directly:

```text
Type: A
Host: @
Value: 110.40.154.41
TTL: automatic or 300 seconds
```

If separate API and static domains are needed later:

```text
papers.wangyutang.com A -> 110.40.154.41
api-papers.wangyutang.com A -> 110.40.154.41
```

## Security Group

Open only:

```text
22/tcp   maintainer IP only
80/tcp   0.0.0.0/0
443/tcp  0.0.0.0/0
```

Do not expose:

```text
8088/tcp
SQLite volume paths
Docker daemon ports
```

## Cloud Files

Cloud deployment files included:

```text
infra/docker-compose.cloud.yml
infra/docker-compose.image.yml
infra/docker-compose.app-only.yml
infra/caddy/Caddyfile
infra/env.cloud.example
```

Server setup shape:

```text
Caddy :80/:443
  -> paper-learning container :8088
  -> SQLite volume
```

## Required Production Settings

Set these in `infra/.env.cloud` on the server:

```text
PAPERS_DOMAIN=papers.wangyutang.com
ACME_EMAIL=admin@wangyutang.com
API_TOKEN=<long random token>
OPENAI_API_KEY=<optional>
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
PYTHON_IMAGE=python:3.12-slim
```

`API_TOKEN` should be treated as a secret. The browser UI has a token field for authenticated deployment.

If Docker Hub is unreachable from the server, set `PYTHON_IMAGE` to a reachable mirror image that is compatible with `python:3.12-slim`, or pre-pull/cache the base image before building.

## Deploy Commands

On the server:

```bash
cd paper_learning_system/infra
cp env.cloud.example .env.cloud
docker compose -f docker-compose.cloud.yml up -d --build
docker compose -f docker-compose.cloud.yml ps
```

If you build the image locally and upload `paper-learning-system_local.tar`:

```bash
cd paper_learning_system/infra
cp env.cloud.example .env.cloud
docker load -i ../paper-learning-system_local.tar
docker compose --env-file .env.cloud -f docker-compose.image.yml up -d
docker compose --env-file .env.cloud -f docker-compose.image.yml ps
```

If the Caddy image cannot be pulled, run only the app container and use host-level Caddy or Nginx:

```bash
docker compose --env-file .env.cloud -f docker-compose.app-only.yml up -d
curl http://127.0.0.1:8088/api/health
```

Check:

```bash
curl https://papers.wangyutang.com/api/health
```

## Backup

SQLite data lives in the `paper_learning_data` Docker volume. Add regular backups before real usage.

Minimum backup checklist:

```text
Nightly SQLite backup
Off-server copy
Restore test
Credential rotation note
```

## Acceptance Criteria

```text
https://papers.wangyutang.com opens the workspace
HTTPS certificate is valid
API rejects requests without the correct Bearer token when API_TOKEN is set
arXiv mining works from the cloud server
manual paper creation works
paper analysis works with local fallback when no LLM key is set
paper analysis works with LLM when OPENAI_API_KEY is set
paper question answering works
practice questions are generated
SQLite volume survives container restart
8088 is not publicly exposed
```
