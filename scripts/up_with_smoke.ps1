#!/usr/bin/env pwsh

docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$timeoutSeconds = 60
$elapsed = 0
$cid = ""

while ($elapsed -lt $timeoutSeconds) {
  $cid = (docker compose ps -a -q smoke) | Select-Object -First 1
  if ($cid) { break }
  Start-Sleep -Seconds 1
  $elapsed++
}

if (-not $cid) {
  Write-Host "Smoke container not found."
  exit 1
}

while ($true) {
  $inspect = docker inspect -f '{{.State.Status}} {{.State.ExitCode}}' $cid
  $parts = $inspect -split ' '
  $state = $parts[0]
  $exitCode = [int]$parts[1]
  if ($state -eq 'exited') { break }
  Start-Sleep -Seconds 1
}

if ($exitCode -ne 0) {
  Write-Host "Smoke test failed. Stopping stack..."
  docker compose down
  exit 1
}

Write-Host "Smoke test passed. Stack is running."
