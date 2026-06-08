#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="stock-ai-monitor"
TEMPLATE_PATH="$ROOT_DIR/deploy/systemd/stock-ai-monitor.service"
TARGET_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found. Please install Docker first."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin not found. Please install docker compose plugin first."
  exit 1
fi

if [ ! -f "$TEMPLATE_PATH" ]; then
  echo "systemd template not found: $TEMPLATE_PATH"
  exit 1
fi

sudo systemctl enable --now docker
sudo mkdir -p /etc/systemd/system
sed "s|__APP_DIR__|$ROOT_DIR|g" "$TEMPLATE_PATH" | sudo tee "$TARGET_PATH" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"

echo
echo "Installed and started systemd service: $SERVICE_NAME"
echo "Check status with:"
echo "  sudo systemctl status $SERVICE_NAME"
