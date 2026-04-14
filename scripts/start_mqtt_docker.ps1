$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
  Write-Error "Docker is not installed or not in PATH. Install Docker Desktop first, then rerun this script."
  exit 1
}

docker compose -f ..\infra\docker-compose.yml up -d
python ..\scripts\check_env.py
