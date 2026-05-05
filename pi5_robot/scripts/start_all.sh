#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m uvicorn services.webui.app:app --host 0.0.0.0 --port "${PI5_ROBOT_PORT:-8093}"
