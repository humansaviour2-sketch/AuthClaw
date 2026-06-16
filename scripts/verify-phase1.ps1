#!/usr/bin/env pwsh
# Phase 1 Verification Script - Validates all services

$ErrorActionPreference = "SilentlyContinue"
$checklist = @()

Write-Host "`n==== AuthClaw Phase 1 - Verification Checklist ====`n" -ForegroundColor Cyan

# 1. Docker & Docker Compose
Write-Host "1. Docker Installation..." -NoNewline
$docker = docker --version 2>&1
if ($docker -match "Docker version") {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="Docker installed"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="Docker installed"; status="FAIL"}
}

Write-Host "2. Docker Compose Installation..." -NoNewline
$compose = docker-compose --version 2>&1
if ($compose -match "Docker Compose version") {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="Docker Compose installed"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="Docker Compose installed"; status="FAIL"}
}

# 2. Services Running
Write-Host "3. PostgreSQL Container..." -NoNewline
$postgres = docker ps --filter "name=authclaw-postgres" --format "table {{.Names}}" | Select-String "postgres"
if ($postgres) {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="PostgreSQL running"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="PostgreSQL running"; status="FAIL"}
}

Write-Host "4. Redis Container..." -NoNewline
$redis = docker ps --filter "name=authclaw-redis" --format "table {{.Names}}" | Select-String "redis"
if ($redis) {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="Redis running"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="Redis running"; status="FAIL"}
}

Write-Host "5. OPA Container..." -NoNewline
$opa = docker ps --filter "name=authclaw-opa" --format "table {{.Names}}" | Select-String "opa"
if ($opa) {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="OPA running"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="OPA running"; status="FAIL"}
}

Write-Host "6. Presidio Container..." -NoNewline
$presidio = docker ps --filter "name=authclaw-presidio" --format "table {{.Names}}" | Select-String "presidio"
if ($presidio) {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="Presidio running"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="Presidio running"; status="FAIL"}
}

# 3. Service Connectivity
Write-Host "7. PostgreSQL Connectivity..." -NoNewline
$pgtest = docker-compose exec -T postgres psql -U authclaw -d authclaw -c "SELECT 1;" 2>&1 | Select-String "1"
if ($pgtest) {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="PostgreSQL query successful"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="PostgreSQL query successful"; status="FAIL"}
}

Write-Host "8. Redis Connectivity..." -NoNewline
$redistest = docker-compose exec -T redis redis-cli ping 2>&1 | Select-String "PONG"
if ($redistest) {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="Redis ping successful"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="Redis ping successful"; status="FAIL"}
}

Write-Host "9. Presidio Health..." -NoNewline
try {
    $presidioHealthResponse = Invoke-WebRequest -Uri "http://localhost:3000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($presidioHealthResponse.StatusCode -eq 200) {
        Write-Host " [PASS]" -ForegroundColor Green
        $checklist += @{task="Presidio accessible"; status="PASS"}
    } else {
        Write-Host " [FAIL]" -ForegroundColor Red
        $checklist += @{task="Presidio accessible"; status="FAIL"}
    }
} catch {
    Write-Host " [WARMUP]" -ForegroundColor Yellow
    $checklist += @{task="Presidio accessible"; status="WARMUP"}
}

# 4. Configuration Files
Write-Host "10. .env.local Exists..." -NoNewline
if (Test-Path ".\.env.local") {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task=".env.local created"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task=".env.local created"; status="FAIL"}
}

Write-Host "11. README.md Exists..." -NoNewline
if (Test-Path ".\README.md") {
    Write-Host " [PASS]" -ForegroundColor Green
    $checklist += @{task="README.md created"; status="PASS"}
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    $checklist += @{task="README.md created"; status="FAIL"}
}
# Summary
Write-Host "`n=============================================`n" -ForegroundColor Cyan

$passed = ($checklist | Where-Object {$_.status -eq "PASS"}).count
$failed = ($checklist | Where-Object {$_.status -eq "FAIL"}).count
$warmup = ($checklist | Where-Object {$_.status -eq "WARMUP"}).count
$total = $checklist.count

Write-Host "SUMMARY:`n" -ForegroundColor Cyan
$checklist | ForEach-Object {
    $symbol = switch($_.status) {
        "PASS" { "OK" }
        "FAIL" { "XX" }
        "WARMUP" { "~~" }
    }
    Write-Host "  [$symbol] $($_.task)"
}

Write-Host "`nTOTALS:`n" -ForegroundColor Cyan
Write-Host "  Passed:  $passed" -ForegroundColor Green
Write-Host "  Failed:  $failed" -ForegroundColor Red
Write-Host "  Warming: $warmup" -ForegroundColor Yellow
Write-Host "  Total:   $total`n"

if ($failed -eq 0) {
    Write-Host "RESULT: PHASE 1 PASSED" -ForegroundColor Green
    Write-Host "`nAll services are running and accessible.`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "RESULT: PHASE 1 INCOMPLETE" -ForegroundColor Yellow
    Write-Host "`nPlease fix the failed checks before proceeding.`n" -ForegroundColor Yellow
    exit 1
}
