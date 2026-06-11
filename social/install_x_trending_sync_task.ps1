param(
  [string]$TaskName = "WorldCup2026XTrendingSync",
  [string]$ProjectRoot = "J:\promotion helper",
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $ProjectRoot "social\sync_x_trending.py"
$runnerPath = Join-Path $ProjectRoot "social\run_x_trending_sync.cmd"
if (-not (Test-Path -LiteralPath $scriptPath)) {
  throw "Cannot find sync script: $scriptPath"
}

$pythonCommand = Get-Command $PythonExe -ErrorAction Stop
$pythonPath = $pythonCommand.Source
if (-not (Test-Path -LiteralPath $pythonPath)) {
  throw "Cannot resolve Python executable: $PythonExe"
}

Set-Content -LiteralPath $runnerPath -Encoding ASCII -Value @(
  "@echo off",
  "cd /d `"$ProjectRoot`"",
  "`"$pythonPath`" `"social\sync_x_trending.py`""
)

$fso = New-Object -ComObject Scripting.FileSystemObject
$runnerShortPath = $fso.GetFile($runnerPath).ShortPath
if (-not $runnerShortPath) {
  throw "Could not resolve short path for runner script: $runnerPath"
}

$token = [Environment]::GetEnvironmentVariable("X_BEARER_TOKEN", "User")
if (-not $token) {
  throw "Set X_BEARER_TOKEN as a User environment variable first."
}

schtasks.exe /Create `
  /TN $TaskName `
  /SC HOURLY `
  /MO 2 `
  /TR $runnerShortPath `
  /F | Out-Host

if ($LASTEXITCODE -ne 0) {
  throw "Failed to create scheduled task. Try running PowerShell as Administrator."
}

Write-Host "Installed scheduled task: $TaskName"
Write-Host "It will run every 2 hours and update social\x-trending-posts.js"
Write-Host "Task action: $runnerShortPath"
Write-Host "You can test it with:"
Write-Host "schtasks.exe /Run /TN $TaskName"
