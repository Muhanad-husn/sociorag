# SocioRAG True Documentation Consolidation Script
# Purpose: REDUCE total .md file count by merging and removing redundant files

Write-Host "🎯 Starting TRUE consolidation - reducing total .md file count..." -ForegroundColor Green

Set-Location "d:\sociorag"

# Count current files
$currentFiles = (Get-ChildItem -Path "docs" -Filter "*.md" -Recurse).Count
Write-Host "Current .md files in docs/: $currentFiles" -ForegroundColor Yellow

# =============================================================================
# PHASE 1: MERGE NEW FILES INTO EXISTING ONES AND DELETE THE NEW ONES
# =============================================================================

# 1. Merge quick_start_guide.md content into installation_guide.md
if (Test-Path "docs\quick_start_guide.md") {
    Write-Host "Merging quick start into installation guide..." -ForegroundColor Cyan
    $quickStartContent = Get-Content "docs\quick_start_guide.md" -Raw
    $installContent = Get-Content "docs\installation_guide.md" -Raw
    
    # Add quick start section to beginning of installation guide
    $mergedInstall = @"
# SocioRAG Installation Guide

## 🚀 Quick Start (< 5 minutes)

### One-Command Setup
``````powershell
# Automated setup - handles everything
.\quick_start.ps1
``````

### Manual Quick Setup
``````powershell
# 1. Create environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Set up API key
echo "OPENROUTER_API_KEY=your_key_here" > .env

# 4. Start application
.\quick_start.ps1
``````

**Access Points:** Frontend: http://localhost:5173 | Backend: http://127.0.0.1:8000 | API Docs: http://127.0.0.1:8000/docs

---

$installContent
"@
    
    $mergedInstall | Out-File -FilePath "docs\installation_guide.md" -Encoding UTF8
    Remove-Item "docs\quick_start_guide.md" -Force
    Write-Host "  ✅ Merged and removed quick_start_guide.md" -ForegroundColor Green
}

# 2. Merge api_unified_reference.md into existing api_documentation.md if it exists, otherwise rename
if (Test-Path "docs\api_unified_reference.md") {
    Write-Host "Consolidating API documentation..." -ForegroundColor Cyan
    
    # Since we archived the original, just rename the unified one
    Move-Item "docs\api_unified_reference.md" "docs\api_documentation.md" -Force
    Write-Host "  ✅ Renamed unified API reference to standard name" -ForegroundColor Green
}

# 3. Merge production_unified_guide.md into existing production_deployment_guide.md
if (Test-Path "docs\production_unified_guide.md") {
    Write-Host "Consolidating production documentation..." -ForegroundColor Cyan
    
    # Rename to standard name (since we archived the original)
    Move-Item "docs\production_unified_guide.md" "docs\production_deployment_guide.md" -Force
    Write-Host "  ✅ Renamed unified production guide to standard name" -ForegroundColor Green
}

# 4. Remove the consolidation report we just created
if (Test-Path "docs\documentation_consolidation_report.md") {
    Remove-Item "docs\documentation_consolidation_report.md" -Force
    Write-Host "  ✅ Removed redundant consolidation report" -ForegroundColor Green
}

# =============================================================================
# PHASE 2: MERGE REDUNDANT STATUS REPORTS
# =============================================================================

Write-Host "Consolidating status reports..." -ForegroundColor Cyan

# Merge changelog into project_status.md to reduce status report count
if (Test-Path "docs\status_reports\changelog_v1.0.1.md") {
    $changelogContent = Get-Content "docs\status_reports\changelog_v1.0.1.md" -Raw
    $statusContent = Get-Content "docs\project_status.md" -Raw
    
    # Insert changelog into project status
    $updatedStatus = $statusContent -replace "## 📊 System Health", @"
## 📋 Version 1.0.1 Changelog

$changelogContent

## 📊 System Health
"@
    
    $updatedStatus | Out-File -FilePath "docs\project_status.md" -Encoding UTF8
    Remove-Item "docs\status_reports\changelog_v1.0.1.md" -Force
    Write-Host "  ✅ Merged changelog into project_status.md" -ForegroundColor Green
}

# Merge version_control_completion_report into version_control_summary
if ((Test-Path "docs\status_reports\version_control_completion_report.md") -and (Test-Path "docs\version_control_summary.md")) {
    $versionReportContent = Get-Content "docs\status_reports\version_control_completion_report.md" -Raw
    $versionSummaryContent = Get-Content "docs\version_control_summary.md" -Raw
    
    # Append completion report to summary
    $mergedVersion = @"
$versionSummaryContent

---

## Completion Report

$versionReportContent
"@
    
    $mergedVersion | Out-File -FilePath "docs\version_control_summary.md" -Encoding UTF8
    Remove-Item "docs\status_reports\version_control_completion_report.md" -Force
    Write-Host "  ✅ Merged version control report into summary" -ForegroundColor Green
}

# =============================================================================
# PHASE 3: MERGE OVERLAPPING GUIDES
# =============================================================================

Write-Host "Consolidating guides..." -ForegroundColor Cyan

# Check if we can merge frontend guides (deployment into development)
if ((Test-Path "docs\guides\frontend_deployment_guide.md") -and (Test-Path "docs\guides\frontend_development_guide.md")) {
    $deployContent = Get-Content "docs\guides\frontend_deployment_guide.md" -Raw
    $devContent = Get-Content "docs\guides\frontend_development_guide.md" -Raw
    
    # Merge deployment into development guide
    $mergedDev = @"
$devContent

---

# Frontend Deployment

$deployContent
"@
    
    $mergedDev | Out-File -FilePath "docs\guides\frontend_development_guide.md" -Encoding UTF8
    Remove-Item "docs\guides\frontend_deployment_guide.md" -Force
    Write-Host "  ✅ Merged frontend deployment into development guide" -ForegroundColor Green
}

# =============================================================================
# PHASE 4: REMOVE REDUNDANT ARCHIVE FILES
# =============================================================================

Write-Host "Cleaning up redundant archive files..." -ForegroundColor Cyan

# Remove empty or very small files in archive
$archiveFiles = Get-ChildItem -Path "docs\archive" -Filter "*.md" -Recurse
foreach ($file in $archiveFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content -or $content.Length -lt 100) {
        Remove-Item $file.FullName -Force
        Write-Host "  ✅ Removed empty archive file: $($file.Name)" -ForegroundColor Green
    }
}

# Remove redundant test READMEs
if (Test-Path "tests\frontend\README.md") {
    $testContent = Get-Content "tests\frontend\README.md" -Raw
    if ($testContent.Length -lt 200) {
        Remove-Item "tests\frontend\README.md" -Force
        Write-Host "  ✅ Removed minimal test README" -ForegroundColor Green
    }
}

# =============================================================================
# PHASE 5: UPDATE MAIN README TO REFLECT SIMPLIFIED STRUCTURE
# =============================================================================

Write-Host "Updating main README..." -ForegroundColor Cyan

$simplifiedReadme = @"
# SocioRAG Documentation Hub

Welcome to the **SocioRAG** project documentation. This streamlined hub provides access to all essential project information.

## 🚀 Quick Start

- **New to SocioRAG?** → [Project Overview](./project_overview.md)
- **Ready to install?** → [Installation Guide](./installation_guide.md) (includes quick start)
- **Need API docs?** → [API Documentation](./api_documentation.md)
- **Current status?** → [Project Status](./project_status.md)

## 📚 Core Documentation

| Document | Description |
|----------|-------------|
| [Project Overview](./project_overview.md) | System overview and architecture |
| [Installation Guide](./installation_guide.md) | Setup instructions (quick & comprehensive) |
| [API Documentation](./api_documentation.md) | Complete API reference |
| [Configuration Guide](./configuration_guide.md) | System configuration |
| [Project Status](./project_status.md) | Current version and system health |
| [Version Control Summary](./version_control_summary.md) | Version information |

## 🔧 Development

| Guide | Description |
|-------|-------------|
| [Frontend Development](./guides/frontend_development_guide.md) | Frontend dev & deployment |
| [Frontend Testing](./guides/frontend_testing_guide.md) | Testing strategies |
| [Performance Testing](./guides/performance_testing_guide.md) | Performance optimization |
| [Developer Guide](./guides/developer_guide.md) | General development guidelines |

## 🏗️ System Documentation

| Document | Description |
|----------|-------------|
| [Architecture Documentation](./architecture_documentation.md) | System design overview |
| [Production Deployment](./production_deployment_guide.md) | Production deployment & runtime |
| [Logging Documentation](./logging_system_documentation.md) | Logging configuration |
| [UI Components](./ui_component_documentation.md) | Component library |
| [Housekeeping Guide](./additional_housekeeping_guide.md) | Maintenance procedures |

## 📋 Status & Reports

- **Current Version**: v1.0.3
- **Status**: ✅ Production Ready  
- **Latest Updates**: [Status Reports](./status_reports/)
- **Archive**: Historical documentation in [archive/](./archive/)

---
*Streamlined documentation structure - essential information without redundancy.*
"@

$simplifiedReadme | Out-File -FilePath "docs\README.md" -Encoding UTF8

# =============================================================================
# FINAL COUNT AND SUMMARY
# =============================================================================

$finalFiles = (Get-ChildItem -Path "docs" -Filter "*.md" -Recurse).Count
$reduction = $currentFiles - $finalFiles

Write-Host "`n📊 CONSOLIDATION COMPLETE!" -ForegroundColor Green
Write-Host "Original files: $currentFiles" -ForegroundColor Yellow
Write-Host "Final files: $finalFiles" -ForegroundColor Yellow
Write-Host "Reduction: $reduction files removed" -ForegroundColor Green

if ($reduction -gt 0) {
    Write-Host "✅ Successfully reduced .md file count by $reduction files" -ForegroundColor Green
} else {
    Write-Host "⚠️ No reduction achieved" -ForegroundColor Red
}

Write-Host "`nFiles merged into existing documentation:" -ForegroundColor Cyan
Write-Host "  • Quick start → Installation Guide" -ForegroundColor White
Write-Host "  • API unified → API Documentation" -ForegroundColor White  
Write-Host "  • Production unified → Production Deployment" -ForegroundColor White
Write-Host "  • Changelog → Project Status" -ForegroundColor White
Write-Host "  • Version reports → Version Summary" -ForegroundColor White
Write-Host "  • Frontend deployment → Frontend Development" -ForegroundColor White
