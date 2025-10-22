#!/usr/bin/env pwsh
# Wiki Setup Script for kAIcad
# This script helps you initialize and publish the kAIcad wiki

Write-Host "`n=== kAIcad Wiki Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if wiki exists
Write-Host "Step 1: Initialize the wiki on GitHub" -ForegroundColor Yellow
Write-Host "---------------------------------------"
Write-Host "The wiki needs to be initialized through GitHub's web interface first."
Write-Host ""
Write-Host "Please follow these steps:"
Write-Host "  1. Open: https://github.com/hunes3d/kAIcad/wiki" -ForegroundColor Green
Write-Host "  2. Click the 'Create the first page' button" -ForegroundColor Green
Write-Host "  3. Add any content (e.g., type '# Welcome')" -ForegroundColor Green
Write-Host "  4. Click 'Save Page'" -ForegroundColor Green
Write-Host ""
$continue = Read-Host "Have you completed these steps? (y/n)"

if ($continue -ne "y") {
    Write-Host "`nPlease complete the wiki initialization first, then run this script again." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Clone the wiki
Write-Host "Step 2: Cloning the wiki repository..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

$wikiDir = Join-Path (Split-Path $PSScriptRoot -Parent) "kAIcad.wiki"

if (Test-Path $wikiDir) {
    Write-Host "Wiki directory already exists. Pulling latest changes..." -ForegroundColor Cyan
    Push-Location $wikiDir
    git pull
    Pop-Location
} else {
    Push-Location (Split-Path $PSScriptRoot -Parent)
    git clone https://github.com/hunes3d/kAIcad.wiki.git
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nFailed to clone wiki. Make sure you've initialized it on GitHub first." -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
}

Write-Host "✓ Wiki repository ready" -ForegroundColor Green
Write-Host ""

# Step 3: Copy wiki content
Write-Host "Step 3: Copying wiki documentation..." -ForegroundColor Yellow
Write-Host "---------------------------------------"

$sourceDir = Join-Path $PSScriptRoot "wiki"
$files = @("Home.md", "Getting-Started.md", "Installation.md", "Features.md")

foreach ($file in $files) {
    $source = Join-Path $sourceDir $file
    $dest = Join-Path $wikiDir $file
    
    if (Test-Path $source) {
        Copy-Item $source $dest -Force
        Write-Host "  ✓ Copied $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Warning: $file not found" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 4: Commit and push
Write-Host "Step 4: Publishing to GitHub..." -ForegroundColor Yellow
Write-Host "---------------------------------"

Push-Location $wikiDir

# Check if there are changes
git add .
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit. Wiki is already up to date." -ForegroundColor Cyan
} else {
    git commit -m "Add comprehensive wiki documentation

- Home page with overview and quick links
- Getting Started guide
- Installation instructions for all platforms
- Complete features documentation"
    
    git push
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Wiki published successfully!" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to push changes" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

Pop-Location

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "✓ Wiki setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "View your wiki at:" -ForegroundColor Cyan
Write-Host "  https://github.com/hunes3d/kAIcad/wiki" -ForegroundColor Green
Write-Host ""
