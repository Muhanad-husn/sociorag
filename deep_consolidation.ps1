# SocioRAG Deep Consolidation - Round 2
# Purpose: Further reduce .md file count by merging more redundant content

Write-Host "🎯 Deep consolidation - Round 2..." -ForegroundColor Green

Set-Location "d:\sociorag"

$currentFiles = (Get-ChildItem -Path "docs" -Filter "*.md" -Recurse).Count
Write-Host "Current .md files: $currentFiles" -ForegroundColor Yellow

# =============================================================================
# MERGE CONFIGURATION & INSTALLATION 
# =============================================================================
Write-Host "Merging configuration into installation guide..." -ForegroundColor Cyan

if ((Test-Path "docs\configuration_guide.md") -and (Test-Path "docs\installation_guide.md")) {
    $configContent = Get-Content "docs\configuration_guide.md" -Raw
    $installContent = Get-Content "docs\installation_guide.md" -Raw
    
    # Add configuration section to installation guide
    $mergedInstall = @"
$installContent

---

# Configuration Guide

$configContent
"@
    
    $mergedInstall | Out-File -FilePath "docs\installation_guide.md" -Encoding UTF8
    Remove-Item "docs\configuration_guide.md" -Force
    Write-Host "  ✅ Merged configuration_guide.md into installation_guide.md" -ForegroundColor Green
}

# =============================================================================
# MERGE HOUSEKEEPING INTO PRODUCTION GUIDE
# =============================================================================
Write-Host "Merging housekeeping into production guide..." -ForegroundColor Cyan

if ((Test-Path "docs\additional_housekeeping_guide.md") -and (Test-Path "docs\production_deployment_guide.md")) {
    $housekeepingContent = Get-Content "docs\additional_housekeeping_guide.md" -Raw
    $productionContent = Get-Content "docs\production_deployment_guide.md" -Raw
    
    # Add housekeeping section to production guide
    $mergedProduction = @"
$productionContent

---

# System Maintenance & Housekeeping

$housekeepingContent
"@
    
    $mergedProduction | Out-File -FilePath "docs\production_deployment_guide.md" -Encoding UTF8
    Remove-Item "docs\additional_housekeeping_guide.md" -Force
    Write-Host "  ✅ Merged housekeeping guide into production guide" -ForegroundColor Green
}

# =============================================================================
# MERGE VERSION CONTROL INTO PROJECT STATUS
# =============================================================================
Write-Host "Merging version control into project status..." -ForegroundColor Cyan

if ((Test-Path "docs\version_control_summary.md") -and (Test-Path "docs\project_status.md")) {
    $versionContent = Get-Content "docs\version_control_summary.md" -Raw
    $statusContent = Get-Content "docs\project_status.md" -Raw
    
    # Add version control section to project status
    $mergedStatus = @"
$statusContent

---

# Version Control Summary

$versionContent
"@
    
    $mergedStatus | Out-File -FilePath "docs\project_status.md" -Encoding UTF8
    Remove-Item "docs\version_control_summary.md" -Force
    Write-Host "  ✅ Merged version control summary into project status" -ForegroundColor Green
}

# =============================================================================
# MERGE UI COMPONENTS INTO ARCHITECTURE
# =============================================================================
Write-Host "Merging UI components into architecture documentation..." -ForegroundColor Cyan

if ((Test-Path "docs\ui_component_documentation.md") -and (Test-Path "docs\architecture_documentation.md")) {
    $uiContent = Get-Content "docs\ui_component_documentation.md" -Raw
    $archContent = Get-Content "docs\architecture_documentation.md" -Raw
    
    # Add UI components section to architecture
    $mergedArch = @"
$archContent

---

# UI Component Documentation

$uiContent
"@
    
    $mergedArch | Out-File -FilePath "docs\architecture_documentation.md" -Encoding UTF8
    Remove-Item "docs\ui_component_documentation.md" -Force
    Write-Host "  ✅ Merged UI components into architecture documentation" -ForegroundColor Green
}

# =============================================================================
# CONSOLIDATE REMAINING STATUS REPORTS
# =============================================================================
Write-Host "Consolidating remaining status reports..." -ForegroundColor Cyan

# Create a single consolidated status report file
$statusReports = Get-ChildItem -Path "docs\status_reports" -Filter "*.md"
if ($statusReports.Count -gt 1) {
    $consolidatedReports = @"
# SocioRAG Status Reports Consolidated

This document consolidates all individual status reports for easier reference.

"@
    
    foreach ($report in $statusReports) {
        $reportContent = Get-Content $report.FullName -Raw
        $reportName = $report.BaseName
        $consolidatedReports += @"

---

## $reportName

$reportContent

"@
    }
    
    $consolidatedReports | Out-File -FilePath "docs\status_reports_consolidated.md" -Encoding UTF8
    
    # Remove individual reports
    foreach ($report in $statusReports) {
        Remove-Item $report.FullName -Force
        Write-Host "  ✅ Consolidated: $($report.Name)" -ForegroundColor Green
    }
    
    # Remove empty status_reports directory
    if ((Get-ChildItem "docs\status_reports" -Force | Measure-Object).Count -eq 0) {
        Remove-Item "docs\status_reports" -Force
        Write-Host "  ✅ Removed empty status_reports directory" -ForegroundColor Green
    }
}

# =============================================================================
# CONSOLIDATE GUIDES INTO DEVELOPER GUIDE
# =============================================================================
Write-Host "Consolidating guides..." -ForegroundColor Cyan

$guideFiles = Get-ChildItem -Path "docs\guides" -Filter "*.md"
if ($guideFiles.Count -gt 1) {
    # Keep developer_guide.md as the main guide and merge others into it
    $developerGuide = "docs\guides\developer_guide.md"
    
    if (Test-Path $developerGuide) {
        $mainContent = Get-Content $developerGuide -Raw
        
        foreach ($guide in $guideFiles) {
            if ($guide.Name -ne "developer_guide.md") {
                $guideContent = Get-Content $guide.FullName -Raw
                $guideName = $guide.BaseName -replace "_", " " -replace "guide", ""
                
                $mainContent += @"

---

# $guideName

$guideContent

"@
                Remove-Item $guide.FullName -Force
                Write-Host "  ✅ Merged $($guide.Name) into developer_guide.md" -ForegroundColor Green
            }
        }
        
        $mainContent | Out-File -FilePath $developerGuide -Encoding UTF8
    }
}

# =============================================================================
# CLEAN UP ARCHIVE - REMOVE SMALLEST FILES
# =============================================================================
Write-Host "Cleaning up minimal archive files..." -ForegroundColor Cyan

$archiveFiles = Get-ChildItem -Path "docs\archive" -Filter "*.md" -Recurse
foreach ($file in $archiveFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content -or $content.Length -lt 500) {
        Remove-Item $file.FullName -Force
        Write-Host "  ✅ Removed minimal archive file: $($file.Name)" -ForegroundColor Green
    }
}

# =============================================================================
# UPDATE MAIN README FOR SIMPLIFIED STRUCTURE
# =============================================================================
Write-Host "Updating main README for new structure..." -ForegroundColor Cyan

$updatedReadme = @"
# SocioRAG Documentation Hub

## 🚀 Quick Access

- **Getting Started** → [Installation Guide](./installation_guide.md)
- **API Reference** → [API Documentation](./api_documentation.md)  
- **System Overview** → [Project Overview](./project_overview.md)
- **Current Status** → [Project Status](./project_status.md)

## 📚 Complete Documentation

### Core Documentation
- [**Installation Guide**](./installation_guide.md) - Setup, configuration, and quick start
- [**API Documentation**](./api_documentation.md) - Complete API reference with examples
- [**Project Overview**](./project_overview.md) - System architecture and features
- [**Project Status**](./project_status.md) - Current version, health, and version control
- [**Architecture Documentation**](./architecture_documentation.md) - System design and UI components

### Production & Development  
- [**Production Deployment Guide**](./production_deployment_guide.md) - Deployment, runtime, and maintenance
- [**Developer Guide**](./guides/developer_guide.md) - All development guides consolidated
- [**Logging Documentation**](./logging_system_documentation.md) - Logging configuration

### Reports & History
- [**Status Reports**](./status_reports_consolidated.md) - All status reports consolidated
- [**Archive**](./archive/) - Historical documentation

## 📊 Project Info

**Version**: v1.0.3 | **Status**: ✅ Production Ready | **Documentation**: Streamlined & Consolidated

---
*Consolidated documentation structure - maximum information, minimum files.*
"@

$updatedReadme | Out-File -FilePath "docs\README.md" -Encoding UTF8

# =============================================================================
# FINAL REPORT
# =============================================================================

$finalFiles = (Get-ChildItem -Path "docs" -Filter "*.md" -Recurse).Count
$reduction = $currentFiles - $finalFiles

Write-Host "`n🎯 DEEP CONSOLIDATION COMPLETE!" -ForegroundColor Green
Write-Host "Files before: $currentFiles" -ForegroundColor Yellow  
Write-Host "Files after: $finalFiles" -ForegroundColor Yellow
Write-Host "Additional reduction: $reduction files" -ForegroundColor Green

Write-Host "`nMerged in this round:" -ForegroundColor Cyan
Write-Host "  • Configuration → Installation Guide" -ForegroundColor White
Write-Host "  • Housekeeping → Production Guide" -ForegroundColor White
Write-Host "  • Version Control → Project Status" -ForegroundColor White
Write-Host "  • UI Components → Architecture" -ForegroundColor White
Write-Host "  • All Status Reports → Single consolidated file" -ForegroundColor White
Write-Host "  • All Guides → Developer Guide" -ForegroundColor White
