param(
  [string]$TaskName = "WorldCup2026CloudflareGrowthSync",
  [string]$ProjectRoot = "J:\promotion helper",
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $ProjectRoot "admin\sync_cloudflare.py"
$runnerPath = Join-Path $ProjectRoot "admin\run_cloudflare_sync.cmd"
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
  "`"$pythonPath`" `"admin\sync_cloudflare.py`""
)

$fso = New-Object -ComObject Scripting.FileSystemObject
$runnerShortPath = $fso.GetFile($runnerPath).ShortPath
if (-not $runnerShortPath) {
  throw "Could not resolve short path for runner script: $runnerPath"
}

$token = [Environment]::GetEnvironmentVariable("CLOUDFLARE_API_TOKEN", "User")
$zone = [Environment]::GetEnvironmentVariable("CLOUDFLARE_ZONE_ID", "User")

if (-not $token -or -not $zone) {
  throw "Set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID as User environment variables first."
}

schtasks.exe /Create `
  /TN $TaskName `
  /SC HOURLY `
  /MO 3 `
  /TR $runnerShortPath `
  /F | Out-Host

if ($LASTEXITCODE -ne 0) {
  throw "Failed to create scheduled task. Try running PowerShell as Administrator, or use admin\start_cloudflare_sync_loop.cmd as a no-admin fallback."
}

Write-Host "Installed scheduled task: $TaskName"
Write-Host "It will run every 3 hours and update admin\growth-data.js"
Write-Host "Task action: $runnerShortPath"
Write-Host "You can test it with:"
Write-Host "schtasks.exe /Run /TN $TaskName"
