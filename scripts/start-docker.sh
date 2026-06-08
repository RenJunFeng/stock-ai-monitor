#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose up -d --build

echo
echo "Docker services are starting:"
echo "Frontend: http://127.0.0.1:51998"
echo "Containers:"
echo "- stock-ai-monitor-web"
echo "- stock-ai-monitor-api"
