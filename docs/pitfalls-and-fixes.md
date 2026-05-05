# 平台维护坑点与解决方法

日期：2026-05-01

## GitHub 推送失败

现象：

```text
fatal: unable to access 'https://github.com/1540530942/MyTest.git/':
Failed to connect to github.com port 443

fatal: unable to access 'https://github.com/1540530942/MyTest.git/':
Recv failure: Connection was reset
```

诊断：

```powershell
Test-NetConnection github.com -Port 443
```

结果显示 `PingSucceeded: True`，但 `TcpTestSucceeded: False`。说明 DNS 和 ICMP 可达，但 Git 默认 HTTPS 连接不稳定。

解决：

```powershell
git -c http.version=HTTP/1.1 -c http.sslBackend=schannel push -u origin feature/llm-manager
```

这次成功推送到：

```text
https://github.com/1540530942/MyTest.git
branch: feature/llm-manager
commit: 94b6f8b Add wangyutang platform llm manager
```

## 新仓库初始化注意

`wangyutang_platform` 原来不是 Git 仓库，直接 `git push` 不可用。

处理步骤：

```powershell
git init
git checkout -b feature/llm-manager
git remote add origin https://github.com/1540530942/MyTest.git
git add .
git commit -m "Add wangyutang platform llm manager"
```

推送前已加入 `.gitignore`，避免提交：

```text
.env
__pycache__/
*.pyc
control_platform/infra/caddy/Caddyfile.server
node_modules/
dist/
build/
```

## 服务器 Docker Hub 拉取超时

现象：

```text
failed to resolve source metadata for docker.io/library/python:3.12-slim
dial tcp ...:443: i/o timeout
```

原因：

服务器访问 Docker Hub 不稳定，构建 `llm_manager/Dockerfile` 时无法拉取 `python:3.12-slim`。

解决：

服务器已有 `control-platform:local` 镜像，且里面已经包含 FastAPI、Uvicorn、httpx、pydantic。新增 `llm_manager/Dockerfile.server`，复用已有镜像作为基础镜像：

```dockerfile
FROM control-platform:local
HEALTHCHECK NONE
WORKDIR /app
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8092"]
```

服务器构建命令：

```bash
docker build -t llm-manager:local -f /root/control_platform/llm_manager/Dockerfile.server /root/control_platform/llm_manager
```

## 继承旧镜像 Healthcheck

现象：

`llm-manager` 接口正常：

```text
curl http://127.0.0.1:8092/api/health
{"status":"ok","providers":0}
```

但容器状态显示 `unhealthy`。

原因：

`Dockerfile.server` 复用了 `control-platform:local`，继承了旧镜像的 healthcheck，检查的不是 `8092`。

解决：

在 `Dockerfile.server` 中加入：

```dockerfile
HEALTHCHECK NONE
```

## Caddyfile 服务器专用文件不能带 BOM

现象：

Caddy 校验报错：

```text
server block without any key is global configuration, and if used, it must be first
```

原因：

PowerShell `Set-Content -Encoding UTF8` 在部分 Windows PowerShell 环境下会写入 UTF-8 BOM，Caddyfile 开头被 BOM 干扰。

解决：

用无 BOM UTF-8 写临时服务器文件：

```powershell
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path .\control_platform\infra\caddy\Caddyfile.server), $src, $encoding)
```

## Caddy 环境变量与重复站点

现象 1：

```text
server block without any key is global configuration
```

原因：

服务器运行的 Caddy 容器没有注入本地 `.env` 中的 `{$WWW_DOMAIN}`、`{$LLM_DOMAIN}` 等变量，直接校验会失败。

解决：

上传服务器前，把变量替换成字面量域名。

现象 2：

```text
ambiguous site definition: http://www.wangyutang.cn
```

原因：

配置里已经有 `http://www.wangyutang.cn` 站点块，再把 `{$WWW_DOMAIN}` 替换成 `http://www.wangyutang.cn` 会重复。

解决：

保留显式 HTTP 主入口，变量域名块替换成 HTTPS 域名，例如：

```text
{$WWW_DOMAIN} -> https://www.wangyutang.cn
{$LLM_DOMAIN} -> https://llm.wangyutang.cn
```

## PowerShell 执行 SSH 命令的日期变量坑

现象：

```text
Get-Date : Cannot bind parameter 'Date'. Cannot convert value "+%Y%m%d-%H%M%S"
```

原因：

Windows PowerShell 会提前解释双引号里的 `$(date +%Y%m%d-%H%M%S)`，导致本来应该在 Linux 服务器上执行的命令被本机 PowerShell 处理。

解决：

外层 SSH 远程命令使用单引号：

```powershell
ssh root@110.40.154.41 'ts=$(date +%Y%m%d-%H%M%S); echo $ts'
```

## SSH 连接限速

现象：

```text
kex_exchange_identification: Connection closed by remote host
```

原因：

短时间内连续 SSH/SCP 连接服务器，远端会临时关闭连接。

解决：

连续操作之间加等待：

```powershell
Start-Sleep -Seconds 10
```

如果已经触发限速，等待 45 到 120 秒后再试。

## bind mount 文件不能 docker cp 覆盖

现象：

直接 `docker cp` 覆盖容器里的注册表文件可能失败，因为它是宿主机 bind mount。

解决：

更新宿主机文件，再重启对应容器：

```bash
cp /tmp/registry.json /root/control_platform/registry.json
docker restart control-platform
```

## 当前可用验证命令

LLM 模块：

```powershell
Invoke-WebRequest -Uri 'http://www.wangyutang.cn/llm/api/health' -UseBasicParsing
Invoke-WebRequest -Uri 'http://www.wangyutang.cn/llm/' -UseBasicParsing
```

Docker Compose 配置：

```powershell
docker compose config --quiet
```

Python 语法：

```powershell
python -m compileall -q .\llm_manager
```
