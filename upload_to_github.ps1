param(
  [string]$Message = "Update World Cup growth assistant",
  [string]$Branch = "master"
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

Write-Host "Repository:" (Get-Location)
Write-Host "Branch:" $Branch

$remote = git remote get-url origin
if (-not $remote) {
  throw "No Git remote named origin was found."
}
Write-Host "Remote origin:" $remote

git status --short

$changes = git status --porcelain
if ($changes) {
  git add --all
  git commit -m $Message
} else {
  Write-Host "No local changes to commit."
}

git pull --rebase origin $Branch
git push origin $Branch

Write-Host "Upload finished."
