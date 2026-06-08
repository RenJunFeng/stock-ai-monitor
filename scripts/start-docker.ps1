$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

docker compose up -d --build

Write-Host ""
Write-Host "Docker services are starting:"
Write-Host "Frontend: http://127.0.0.1:51998"
Write-Host "Containers:"
Write-Host "- stock-ai-monitor-web"
Write-Host "- stock-ai-monitor-api"
