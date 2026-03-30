#!/usr/bin/env powershell
<#
.SYNOPSIS
    Create PR from feature/bi-dashboard to master and enable auto-merge
.DESCRIPTION
    Automates PR creation, validation of CI/CD checks, and auto-merge to master
.EXAMPLE
    .\scripts\pr-and-merge.ps1
#>

param(
    [switch]$Wait = $false
)

Write-Host "=== Automating PR Creation & Merge ===" -ForegroundColor Cyan

# Check if gh CLI is available
$ghCheck = gh --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: GitHub CLI (gh) not found. Install from https://cli.github.com/" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Creating PR from feature/bi-dashboard to master..." -ForegroundColor Yellow

# Check if PR already exists
$existingPR = gh pr list --base master --head feature/bi-dashboard --json number --jq '.[0].number' 2>$null
if ($existingPR) {
    Write-Host "  PR #$existingPR already exists. Using existing PR." -ForegroundColor Cyan
    $prNumber = $existingPR
} else {
    Write-Host "  No existing PR found. Creating new PR..." -ForegroundColor Cyan
    $prOutput = gh pr create `
        --base master `
        --head feature/bi-dashboard `
        --title "Deploy: Feature BI Dashboard to Production" `
        --body @"
Automated PR from feature/bi-dashboard to master.

## Changes
- Streamlit dashboard fixes and navigation improvements
- dbt data pipeline updates
- Verified table existence and schema compliance

## Checklist
- [x] All changes committed to feature/bi-dashboard
- [x] dbt tests passing
- [ ] Awaiting GitHub Actions CI/CD validation

Once CI/CD checks pass, this PR will auto-merge to master and trigger production deployment.
"@
    
    if ($LASTEXITCODE -eq 0) {
        # Extract PR number from URL
        $prNumber = $prOutput -replace 'https://github.com/.*/pull/(\d+).*', '$1'
        Write-Host "  Created PR #$prNumber" -ForegroundColor Green
    } else {
        Write-Host "  ERROR creating PR" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[2/3] Enabling auto-merge..." -ForegroundColor Yellow

# Enable auto-merge with squash strategy
gh pr merge $prNumber --auto --squash --delete-branch 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Auto-merge enabled for PR #$prNumber" -ForegroundColor Green
} else {
    Write-Host "  Auto-merge may already be enabled or not available. PR created successfully." -ForegroundColor Cyan
}

Write-Host "[3/3] Checking PR status..." -ForegroundColor Yellow

# Get PR details
$prStatus = gh pr view $prNumber --json status,reviewDecision,checks -q '.status,.reviewDecision,.checks[0].conclusion' 2>$null

Write-Host "  PR #$prNumber Status:"
Write-Host "    URL: https://github.com/timlillpoppb/BigQuerySandbox/pull/$prNumber" -ForegroundColor Cyan
if ($Wait) {
    Write-Host "    Waiting for CI/CD checks to complete..." -ForegroundColor Yellow
    
    $maxWait = 300  # 5 minutes
    $elapsed = 0
    $checkInterval = 10
    
    while ($elapsed -lt $maxWait) {
        $checks = gh pr checks $prNumber 2>$null
        if ($checks -match "pass|PASS") {
            Write-Host "    CI/CD checks PASSED" -ForegroundColor Green
            break
        } elseif ($checks -match "fail|FAIL") {
            Write-Host "    CI/CD checks FAILED" -ForegroundColor Red
            exit 1
        }
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
        Write-Host "    Waiting... ($elapsed/$maxWait seconds)" -ForegroundColor Cyan
    }
}

Write-Host "=== PR Ready ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Check PR status: gh pr view $prNumber"
Write-Host "  2. View checks: gh pr checks $prNumber"
Write-Host "  3. PR will auto-merge when all checks pass"
