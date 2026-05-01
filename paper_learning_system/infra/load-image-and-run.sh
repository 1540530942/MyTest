#!/usr/bin/env bash
set -euo pipefail

IMAGE_ARCHIVE="${1:-../paper-learning-system_local.tar}"

if [ ! -f ".env.cloud" ]; then
  cp env.cloud.example .env.cloud
  echo "Created infra/.env.cloud from env.cloud.example. Edit domain, email, API_TOKEN, and image settings before public launch."
fi

docker load -i "$IMAGE_ARCHIVE"
docker compose --env-file .env.cloud -f docker-compose.image.yml up -d
docker compose --env-file .env.cloud -f docker-compose.image.yml ps
