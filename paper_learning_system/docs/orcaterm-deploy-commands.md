# OrcaTerm Deploy Commands

Target:

```text
Instance: lhins-cfcgqi2u
Region: ap-shanghai
OS: OpenCloudOS 9
User: root
App domain: papers.wangyutang.com
Server IP: 110.40.154.41
```

Before running these commands, upload `dist/cloud_bundle` to the server, for example under:

```text
/root/paper_learning_system
```

In Tencent Cloud OrcaTerm, run:

```bash
cd /root/paper_learning_system/infra
chmod +x server-setup-opencloudos.sh load-image-and-run.sh
./server-setup-opencloudos.sh
cp env.cloud.example .env.cloud
python3 - <<'PY'
from pathlib import Path
import secrets

path = Path(".env.cloud")
text = path.read_text()
token = secrets.token_urlsafe(40)
text = text.replace("API_TOKEN=replace-with-a-long-random-token", f"API_TOKEN={token}")
path.write_text(text)
print("API_TOKEN generated and written to .env.cloud")
PY
docker load -i ../paper-learning-system_local.tar
docker compose --env-file .env.cloud -f docker-compose.image.yml up -d
docker compose --env-file .env.cloud -f docker-compose.image.yml ps
curl http://127.0.0.1:8088/api/health
```

If Caddy cannot be pulled, run only the app container:

```bash
docker compose --env-file .env.cloud -f docker-compose.app-only.yml up -d
docker compose --env-file .env.cloud -f docker-compose.app-only.yml ps
curl http://127.0.0.1:8088/api/health
```

After DNS and HTTPS are ready:

```bash
curl https://papers.wangyutang.com/api/health
```
