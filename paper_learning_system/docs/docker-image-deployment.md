# Docker Image Deployment

This project supports two deployment modes:

```text
Mode A: build on the server
  docker compose -f infra/docker-compose.cloud.yml up -d --build

Mode B: build locally, upload image tar, run on the server
  docker load -i paper-learning-system_local.tar
  docker compose --env-file .env.cloud -f docker-compose.image.yml up -d
```

## Local Build

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker_build.ps1
powershell -ExecutionPolicy Bypass -File scripts\docker_export.ps1
powershell -ExecutionPolicy Bypass -File scripts\package_cloud_bundle.ps1
```

Current local image name:

```text
paper-learning-system:local
```

The exported tar is:

```text
dist\paper-learning-system_local.tar
```

## Cloud Server With Image Tar

Upload these to the server:

```text
paper-learning-system_local.tar
infra/
```

For this deployment target:

```text
Server IP: 110.40.154.41
SSH username: root
Region: ap-shanghai
OS: OpenCloudOS 9
Public URL: https://papers.wangyutang.com
```

You can use the Tencent Cloud OrcaTerm web terminal:

```text
https://orcaterm.cloud.tencent.com/terminal?type=lighthouse&instanceId=lhins-cfcgqi2u&region=ap-shanghai&from=lh_console_login_btn
```

Then run:

```bash
cd infra
chmod +x server-setup-opencloudos.sh load-image-and-run.sh
./server-setup-opencloudos.sh
cp env.cloud.example .env.cloud
vim .env.cloud
docker load -i ../paper-learning-system_local.tar
docker compose --env-file .env.cloud -f docker-compose.image.yml up -d
docker compose --env-file .env.cloud -f docker-compose.image.yml ps
```

If the Caddy image cannot be pulled on the server, run only the app container:

```bash
docker compose --env-file .env.cloud -f docker-compose.app-only.yml up -d
curl http://127.0.0.1:8088/api/health
```

Then point host-level Caddy or Nginx to:

```text
http://127.0.0.1:8088
```

## Required .env.cloud Values

```text
PAPERS_DOMAIN=papers.wangyutang.com
ACME_EMAIL=admin@wangyutang.com
PAPER_LEARNING_IMAGE=paper-learning-system:local
API_TOKEN=<long random token>
OPENAI_API_KEY=<optional>
```

For a domain purchased on Spaceship, create this DNS record before checking HTTPS:

```text
Type: A
Host: papers
Value: 110.40.154.41
```

If the chosen public URL is the root domain, use host `@` instead of `papers`.

If building on the server and Docker Hub is blocked, set:

```text
PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.12-slim
```

If using containerized Caddy and Docker Hub is blocked, set `CADDY_IMAGE` to a reachable Caddy-compatible image.
