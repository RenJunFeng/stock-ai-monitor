$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $root ".run"
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$backendPidFile = Join-Path $runDir "backend.pid"
$frontendPidFile = Join-Path $runDir "frontend.pid"

New-Item -ItemType Directory -Path $runDir -Force | Out-Null

function Test-ProcessRunning {
    param([string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        return $false
    }

    $pidValue = Get-Content $PidFile -ErrorAction SilentlyContinue
    if (-not $pidValue) {
        return $false
    }

    return $null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
}

function Start-ManagedProcess {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$PidFile
    )

    if (Test-ProcessRunning $PidFile) {
        Write-Host "$Name is already running."
        return
    }

    $process = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList "-NoLogo", "-NoProfile", "-Command", "Set-Location '$WorkingDirectory'; $Command" `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -Path $PidFile -Value $process.Id
    Write-Host "$Name started. PID: $($process.Id)"
}

if (-not (Test-Path (Join-Path $backendDir ".venv\\Scripts\\python.exe"))) {
    throw "Backend virtual environment not found. Please set up backend/.venv first."
}

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    throw "Frontend dependencies not found. Please run npm install in the frontend directory first."
}

Start-ManagedProcess `
    -Name "Backend" `
    -WorkingDirectory $backendDir `
    -Command ".\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
    -PidFile $backendPidFile

Start-Sleep -Seconds 3

Start-ManagedProcess `
    -Name "Frontend" `
    -WorkingDirectory $frontendDir `
    -Command "npm run dev -- --host 127.0.0.1 --port 5173" `
    -PidFile $frontendPidFile

Write-Host ""
Write-Host "Local services are starting:"
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8000/api/health"
