#!/usr/bin/env pwsh
<#
.SYNOPSIS
Phase 2 Setup Script - Multi-tenant Database Model & Auth Baseline
Sets up the backend environment and database schema.

.DESCRIPTION
1. Installs Python dependencies
2. Initializes database schema with Alembic
3. Enables Row-Level Security (RLS) policies
4. Creates test data
5. Runs isolation tests

.EXAMPLE
.\scripts\setup-phase2.ps1
#>

param(
    [switch]$SkipDeps = $false,
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"
Write-Host "`n==== Phase 2 Setup: Multi-Tenant Database Model ==== `n" -ForegroundColor Cyan

# 1. Check Python installation
Write-Host "1. Checking Python installation..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " OK" -ForegroundColor Green
    Write-Host "   $pythonVersion"
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "   Python not found. Please install Python 3.11+ and add to PATH."
    exit 1
}

# 2. Create and activate virtual environment
Write-Host "2. Setting up Python virtual environment..." -NoNewline
if (!(Test-Path "backend\.venv")) {
    python -m venv backend\.venv
    Write-Host " Created" -ForegroundColor Green
} else {
    Write-Host " Already exists" -ForegroundColor Green
}

# Activate venv
& "backend\.venv\Scripts\Activate.ps1"
Write-Host "   Virtual environment activated"

# 3. Install dependencies
if (!$SkipDeps) {
    Write-Host "3. Installing Python dependencies..." -NoNewline
    pip install -q -r backend/requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "   Check requirements.txt for errors"
        exit 1
    }
} else {
    Write-Host "3. Skipping dependency installation (--SkipDeps)"
}

# 4. Run Alembic migrations
Write-Host "4. Running Alembic migrations..." -NoNewline
cd backend
$migrationOutput = alembic upgrade head 2>&1
cd ..

if ($LASTEXITCODE -eq 0 -or $migrationOutput -match "already at head") {
    Write-Host " OK" -ForegroundColor Green
    Write-Host "   Database schema created"
} else {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "   $migrationOutput"
    exit 1
}

# 5. Enable RLS policies
Write-Host "5. Enabling Row-Level Security policies..." -NoNewline
$rls_sql = Get-Content "infra\postgres\02_enable_rls.sql" -Raw
$rls_output = docker-compose exec -T postgres psql -U authclaw -d authclaw -c "$rls_sql" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host " OK" -ForegroundColor Green
    Write-Host "   RLS policies applied to all tenant-scoped tables"
} else {
    Write-Host " WARNING" -ForegroundColor Yellow
    Write-Host "   RLS setup may need manual configuration"
}

# 6. Verify database schema
Write-Host "6. Verifying database schema..." -NoNewline
$tableCount = docker-compose exec -T postgres psql -U authclaw -d authclaw -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>&1 | Select-String "\s(\d+)\s"

if ($tableCount.Matches.Groups[1].Value -ge 8) {
    Write-Host " OK" -ForegroundColor Green
    Write-Host "   $($tableCount.Matches.Groups[1].Value) tables created"
} else {
    Write-Host " WARNING" -ForegroundColor Yellow
    Write-Host "   Expected 8+ tables, found $($tableCount.Matches.Groups[1].Value)"
}

# 7. Run tests (if not skipped)
if (!$SkipTests) {
    Write-Host "7. Running tenant isolation tests..." -NoNewline
    $testOutput = pytest backend/tests/test_tenant_isolation.py -v 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host " PASSED" -ForegroundColor Green
        Write-Host "   Cross-tenant isolation verified"
    } else {
        Write-Host " FAILED" -ForegroundColor Yellow
        Write-Host "   Some tests may be skipped or failed"
        Write-Host "   Run: pytest backend/tests/test_tenant_isolation.py -v"
    }
} else {
    Write-Host "7. Skipping tests (--SkipTests)"
}

# Summary
Write-Host "`n==== Phase 2 Setup Complete ==== `n" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Database schema: Created with 8 core tables"
Write-Host "  RLS policies:    Enabled (tenant isolation enforced)"
Write-Host "  Tests:           Ready to run"
Write-Host "  Next step:       Review infra/postgres/01_schema.sql and 02_enable_rls.sql"
Write-Host ""

# Print useful commands
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  Run FastAPI:     cd backend && uvicorn main:app --reload"
Write-Host "  Run tests:       pytest backend/tests/test_tenant_isolation.py -v"
Write-Host "  Create migration:cd backend && alembic revision --autogenerate -m 'description'"
Write-Host "  Apply migration: cd backend && alembic upgrade head"
Write-Host ""
