param(
  [string]$TaskName = "SignalWatch Material Refresh",
  [int]$LookbackHours = 24
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$RunnerPath = Join-Path $RepoRoot "scripts\run_material_refresh_scheduled.ps1"

if (-not (Test-Path -LiteralPath $RunnerPath)) {
  throw "Scheduled refresh runner not found: $RunnerPath"
}

$escapedRunner = $RunnerPath.Replace('"', '\"')
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$escapedRunner`" -LookbackHours $LookbackHours"

$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument $arguments `
  -WorkingDirectory $RepoRoot

$triggers = @(
  (New-ScheduledTaskTrigger -Daily -At "07:00")
  (New-ScheduledTaskTrigger -Daily -At "13:00")
)

$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -MultipleInstances IgnoreNew

$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

$principal = New-ScheduledTaskPrincipal `
  -UserId $CurrentUser `
  -LogonType Interactive `
  -RunLevel Limited

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $action `
  -Trigger $triggers `
  -Settings $settings `
  -Principal $principal `
  -Description "Runs SignalWatch evidence collection, signal extraction, and 24-hour material notification refresh at 07:00 and 13:00." `
  -Force | Out-Null

Write-Output "Installed scheduled task '$TaskName' for 07:00 and 13:00 with a $LookbackHours-hour lookback."
