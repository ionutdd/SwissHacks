param(
  [int]$LookbackHours = 24
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $RepoRoot "logs"
$LogPath = Join-Path $LogDir "material_refresh.log"

if (-not (Test-Path -LiteralPath $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Set-Location -LiteralPath $RepoRoot

function Write-RefreshLog {
  param([string]$Value)
  $Value | Out-File -LiteralPath $LogPath -Append -Encoding utf8
}

$startedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
Write-RefreshLog ""
Write-RefreshLog "[$startedAt] Starting SignalWatch material refresh. LookbackHours=$LookbackHours"

& python "scripts\run_material_signal_refresh.py" --lookback-hours $LookbackHours *>&1 | ForEach-Object {
  $line = $_.ToString()
  Write-Output $line
  Write-RefreshLog $line
}

$exitCode = $LASTEXITCODE
$finishedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
Write-RefreshLog "[$finishedAt] Finished SignalWatch material refresh. ExitCode=$exitCode"

exit $exitCode
