# SocioRAG Implementation and Completion Reports Cleanup
# Date: June 1, 2025
# Purpose: Remove all implementation and completion reports except phases 8 and 9

Write-Host "🗑️ Starting cleanup of implementation and completion reports..." -ForegroundColor Red

# Set working directory
Set-Location "d:\sociorag"

# Create final backup before cleanup
$backupDir = "reports_cleanup_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "Creating backup: $backupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item -Path "docs" -Destination "$backupDir\docs_before_cleanup" -Recurse -Force

$removedCount = 0

# =============================================================================
# PHASE 1: REMOVE ALL COMPLETION REPORTS (EXCEPT PHASE 8/9)
# =============================================================================
Write-Host "`n📊 Phase 1: Removing completion reports..." -ForegroundColor Cyan

$completionReports = @(
    "docs\archive\completion_reports\arabic_rtl_implementation_completion_report.md",
    "docs\archive\completion_reports\sociorag_optimization_completion_report.md", 
    "docs\archive\completion_reports\phase7_housekeeping_completion_report.md",
    "docs\archive\completion_reports\pdf_generation_user_choice_completion_report.md",
    "docs\archive\completion_reports\markdown_rendering_redundancy_fix_completion_report.md",
    "docs\archive\completion_reports\markdown_enhancement_completion_report.md",
    "docs\archive\completion_reports\documentation_reorganization_completion_report.md",
    "docs\archive\completion_reports\history_delete_functionality_documentation_completion.md",
    "docs\archive\completion_reports\cleanup_optimization_summary.md",
    "docs\archive\completion_reports\logging_documentation_update_summary.md",
    "docs\archive\completion_reports\pdf_migration_documentation_update_summary.md",
    "docs\archive\completion_reports\playwright_pdf_migration_success_report.md",
    "docs\archive\completion_reports\STREAMING_REMOVAL_SUMMARY.md",
    "docs\archive\completion_reports\test_cleanup_completion_summary.md",
    "docs\archive\completion_reports\unicode_encoding_fix_report.md",
    "docs\archive\completion_reports\phase7_final_production_readiness_report.md",
    "docs\archive\completion_reports\phase7_final_testing_report.md"
)

foreach ($report in $completionReports) {
    if (Test-Path $report) {
        Remove-Item -Path $report -Force
        Write-Host "  Removed: $(Split-Path -Leaf $report)" -ForegroundColor Gray
        $removedCount++
    }
}

# =============================================================================
# PHASE 2: REMOVE ALL PHASE SUMMARIES (EXCEPT PHASE 8/9)
# =============================================================================
Write-Host "`n📋 Phase 2: Removing phase summaries..." -ForegroundColor Cyan

$phaseSummaries = @(
    "docs\archive\phase_summaries\phase5_implementation_summary.md",
    "docs\archive\phase_summaries\phase5_preparation.md",
    "docs\archive\phase_summaries\phase6_housekeeping_summary.md",
    "docs\archive\phase_summaries\phase6_implementation_plan.md",
    "docs\archive\phase_summaries\phase6_implementation_summary.md",
    "docs\archive\phase_summaries\phase6_progress_status_report.md",
    "docs\archive\phase_summaries\phase7_implementation_summary.md",
    "docs\archive\phase_summaries\phase7_implementation_plan.md",
    "docs\archive\phase_summaries\phase7_housekeeping_summary.md",
    "docs\archive\phase_summaries\phase7_housekeeping_assessment.md",
    "docs\archive\phase_summaries\phase7_documentation_package_complete.md"
)

foreach ($summary in $phaseSummaries) {
    if (Test-Path $summary) {
        Remove-Item -Path $summary -Force
        Write-Host "  Removed: $(Split-Path -Leaf $summary)" -ForegroundColor Gray
        $removedCount++
    }
}

# =============================================================================
# PHASE 3: REMOVE ALL PHASE 4 HISTORICAL REPORTS
# =============================================================================
Write-Host "`n🗂️ Phase 3: Removing Phase 4 historical reports..." -ForegroundColor Cyan

$phase4Reports = @(
    "docs\archive\historical\phase4_reports\phase4_validation_summary.md",
    "docs\archive\historical\phase4_reports\phase4_final_validation_summary.md", 
    "docs\archive\historical\phase4_reports\phase4_extended_implementation_summary.md",
    "docs\archive\historical\phase4_reports\phase4_completion_summary.md",
    "docs\archive\historical\phase4_reports\phase4_final_completion_report.md",
    "docs\archive\historical\phase4_reports\phase4_cleanup_completion_report.md"
)

foreach ($report in $phase4Reports) {
    if (Test-Path $report) {
        Remove-Item -Path $report -Force
        Write-Host "  Removed: $(Split-Path -Leaf $report)" -ForegroundColor Gray
        $removedCount++
    }
}

# Remove empty phase4_reports directory
if (Test-Path "docs\archive\historical\phase4_reports") {
    $remainingFiles = Get-ChildItem "docs\archive\historical\phase4_reports" -File
    if ($remainingFiles.Count -eq 0) {
        Remove-Item -Path "docs\archive\historical\phase4_reports" -Force
        Write-Host "  Removed empty directory: phase4_reports" -ForegroundColor Gray
    }
}

# =============================================================================
# PHASE 4: REMOVE STATUS REPORTS (KEEP ONLY CURRENT ONES)
# =============================================================================
Write-Host "`n📈 Phase 4: Cleaning up status reports..." -ForegroundColor Cyan

$statusReportsToRemove = @(
    "docs\status_reports\version_control_completion_report.md",
    "docs\status_reports\model_selection_ui_completion_report.md",
    "docs\status_reports\llm_settings_api_test_report.md",
    "docs\status_reports\import_fix_consolidated_report.md",
    "docs\status_reports\changelog_v1.0.1.md"
)

foreach ($report in $statusReportsToRemove) {
    if (Test-Path $report) {
        Remove-Item -Path $report -Force
        Write-Host "  Removed: $(Split-Path -Leaf $report)" -ForegroundColor Gray
        $removedCount++
    }
}

# =============================================================================
# PHASE 5: REMOVE ADDITIONAL REDUNDANT REPORTS
# =============================================================================
Write-Host "`n🧹 Phase 5: Removing additional redundant reports..." -ForegroundColor Cyan

$additionalReports = @(
    "docs\archive\retriever_test_suite_guide.md",
    "docs\archive\retriever_test_refactoring_report.md",
    "docs\version_control_summary.md"
)

foreach ($report in $additionalReports) {
    if (Test-Path $report) {
        Remove-Item -Path $report -Force
        Write-Host "  Removed: $(Split-Path -Leaf $report)" -ForegroundColor Gray
        $removedCount++
    }
}

# =============================================================================
# PHASE 6: CLEAN UP EMPTY DIRECTORIES
# =============================================================================
Write-Host "`n📁 Phase 6: Cleaning up empty directories..." -ForegroundColor Cyan

$directoriesToCheck = @(
    "docs\archive\phase_summaries",
    "docs\archive\completion_reports",
    "docs\archive\historical\entity_extraction",
    "docs\archive\historical\version_control_updates",
    "docs\status_reports"
)

foreach ($dir in $directoriesToCheck) {
    if (Test-Path $dir) {
        $remainingFiles = Get-ChildItem $dir -File -Recurse
        if ($remainingFiles.Count -eq 0) {
            Remove-Item -Path $dir -Recurse -Force
            Write-Host "  Removed empty directory: $(Split-Path -Leaf $dir)" -ForegroundColor Gray
        } else {
            Write-Host "  Keeping directory with $($remainingFiles.Count) files: $(Split-Path -Leaf $dir)" -ForegroundColor Yellow
        }
    }
}

# =============================================================================
# PHASE 7: CREATE SUMMARY
# =============================================================================
Write-Host "`n📊 Phase 7: Creating cleanup summary..." -ForegroundColor Cyan

$cleanupSummary = @"
# Implementation and Completion Reports Cleanup Summary

**Date:** $(Get-Date -Format "MMMM d, yyyy")  
**Operation:** Removed all implementation and completion reports except phases 8 and 9  
**Backup Location:** $backupDir

## Cleanup Results

- **Total Files Removed:** $removedCount
- **Preserved:** No phase 8 or 9 reports found (none existed)
- **Backup Created:** Yes, in $backupDir

## Categories Cleaned

### ✅ Completion Reports Removed
- Arabic RTL implementation
- SocioRAG optimization  
- Phase 7 housekeeping
- PDF generation improvements
- Markdown rendering fixes
- Documentation reorganization
- History delete functionality
- Cleanup optimization summaries
- Logging documentation updates
- PDF migration reports
- Playwright PDF migration
- Streaming removal summary
- Test cleanup completion
- Unicode encoding fixes
- Phase 7 final reports

### ✅ Phase Summaries Removed
- Phase 5 implementation and preparation
- Phase 6 implementation, housekeeping, and progress reports
- Phase 7 implementation, housekeeping, and assessment reports

### ✅ Historical Reports Removed
- All Phase 4 completion and validation reports
- Retriever test suite and refactoring reports
- Version control completion reports

### ✅ Status Reports Cleaned
- Import fix consolidated reports
- Model selection UI completion
- LLM settings API test reports
- Version control completion reports
- Changelog v1.0.1

## Current Documentation State

The documentation now focuses on:
- **Active Guides:** Installation, API, Production, Development
- **Current Status:** Project status and architecture documentation
- **Essential References:** Configuration and component documentation

## Future Phase 8/9 Reports

When phase 8 and 9 implementation and completion reports are created, they will be the only historical reports maintained in the archive structure.

---
*This cleanup significantly reduces documentation maintenance overhead while preserving all essential operational information.*
"@

$cleanupSummary | Out-File -FilePath "docs\reports_cleanup_summary.md" -Encoding UTF8

# =============================================================================
# FINAL STATUS
# =============================================================================
Write-Host "`n✅ Cleanup completed successfully!" -ForegroundColor Green
Write-Host "📊 Total files removed: $removedCount" -ForegroundColor Cyan
Write-Host "💾 Backup created: $backupDir" -ForegroundColor Cyan
Write-Host "📄 Summary created: docs\reports_cleanup_summary.md" -ForegroundColor Cyan

Write-Host "`n🎯 Documentation is now streamlined for essential operations only." -ForegroundColor Green
Write-Host "   Phase 8 and 9 reports will be preserved when created." -ForegroundColor Yellow

# Show current documentation structure
Write-Host "`n📁 Current docs structure:" -ForegroundColor Yellow
Get-ChildItem "docs" -Recurse -File -Name | Sort-Object
