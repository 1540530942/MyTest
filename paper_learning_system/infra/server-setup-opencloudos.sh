#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root on OpenCloudOS 9." >&2
  exit 1
fi

echo "==> OpenCloudOS release"
cat /etc/os-release || true

echo "==> Installing Docker if needed"
if ! command -v docker >/dev/null 2>&1; then
  dnf install -y yum-utils
  dnf install -y docker docker-compose-plugin || dnf install -y moby-engine docker-compose-plugin
  systemctl enable --now docker
else
  systemctl enable --now docker || true
fi

echo "==> Docker version"
docker --version
docker compose version

echo "==> Opening firewall ports if firewalld is active"
if systemctl is-active --quiet firewalld; then
  firewall-cmd --permanent --add-service=http
  firewall-cmd --permanent --add-service=https
  firewall-cmd --reload
fi

echo "==> Done. Next:"
echo "1. Put paper-learning-system_local.tar next to this infra directory."
echo "2. cp env.cloud.example .env.cloud"
echo "3. Edit .env.cloud: API_TOKEN and optional OPENAI_API_KEY."
echo "4. docker load -i ../paper-learning-system_local.tar"
echo "5. docker compose --env-file .env.cloud -f docker-compose.image.yml up -d"
