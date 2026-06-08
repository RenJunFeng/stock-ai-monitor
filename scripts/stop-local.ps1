$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $root ".run"
$pidFiles = @(
    @{ Name = "Frontend"; Path = (Join-Path $runDir "frontend.pid") },
    @{ Name = "Backend"; Path = (Join-Path $runDir "backend.pid") }
)

foreach ($item in $pidFiles) {
    if (-not (Test-Path $item.Path)) {
        Write-Host "$($item.Name) is not running."
        continue
    }

    $pidValue = Get-Content $item.Path -ErrorAction SilentlyContinue
    if ($pidValue) {
        $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $pidValue -Force
            Write-Host "$($item.Name) stopped."
        } else {
            Write-Host "$($item.Name) process was already gone."
        }
    }

    Remove-Item $item.Path -Force -ErrorAction SilentlyContinue
}
