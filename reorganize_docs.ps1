# SocioRAG Documentation Reorganization Script
# Date: June 1, 2025

Write-Host "🗂️ Starting documentation reorganization..." -ForegroundColor Green

# Set working directory
Set-Location "d:\sociorag"

# Create archive structure
Write-Host "Creating archive directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "docs\archive\completion_reports" -Force | Out-Null
New-Item -ItemType Directory -Path "docs\archive\phase_summaries" -Force | Out-Null
New-Item -ItemType Directory -Path "docs\archive\historical" -Force | Out-Null
New-Item -ItemType Directory -Path "docs\guides" -Force | Out-Null

# Archive completion reports
Write-Host "Moving completion reports to archive..." -ForegroundColor Yellow
$completionReports = @(
    "arabic_rtl_implementation_completion_report.md",
    "history_delete_functionality_documentation_completion.md",
    "markdown_rendering_redundancy_fix_completion_report.md",
    "pdf_generation_user_choice_completion_report.md",
    "playwright_pdf_migration_success_report.md",
    "sociorag_optimization_completion_report.md",
    "unicode_encoding_fix_report.md",
    "phase7_housekeeping_completion_report.md",
    "phase7_final_production_readiness_report.md",
    "phase7_final_testing_report.md",
    "test_cleanup_completion_summary.md"
)

foreach ($report in $completionReports) {
    if (Test-Path "docs\$report") {
        Move-Item -Path "docs\$report" -Destination "docs\archive\completion_reports\" -Force
        Write-Host "  Moved: $report" -ForegroundColor Gray
    }
}

# Archive phase summaries and plans
Write-Host "Moving phase summaries to archive..." -ForegroundColor Yellow
$phaseDocs = @(
    "phase5_implementation_summary.md",
    "phase5_preparation.md",
    "phase6_housekeeping_summary.md",
    "phase6_implementation_plan.md",
    "phase6_implementation_summary.md",
    "phase6_progress_status_report.md",
    "phase7_documentation_package_complete.md",
    "phase7_housekeeping_assessment.md",
    "phase7_housekeeping_summary.md",
    "phase7_implementation_plan.md",
    "phase7_implementation_summary.md"
)

foreach ($phase in $phaseDocs) {
    if (Test-Path "docs\$phase") {
        Move-Item -Path "docs\$phase" -Destination "docs\archive\phase_summaries\" -Force
        Write-Host "  Moved: $phase" -ForegroundColor Gray
    }
}

# Archive summary and optimization reports
Write-Host "Moving summary reports to archive..." -ForegroundColor Yellow
$summaryReports = @(
    "cleanup_optimization_summary.md",
    "logging_documentation_update_summary.md",
    "pdf_migration_documentation_update_summary.md",
    "STREAMING_REMOVAL_SUMMARY.md"
)

foreach ($summary in $summaryReports) {
    if (Test-Path "docs\$summary") {
        Move-Item -Path "docs\$summary" -Destination "docs\archive\completion_reports\" -Force
        Write-Host "  Moved: $summary" -ForegroundColor Gray
    }
}

# Move development guides to guides folder
Write-Host "Organizing development guides..." -ForegroundColor Yellow
$guides = @(
    "frontend_development_guide.md",
    "frontend_testing_guide.md",
    "frontend_deployment_guide.md",
    "performance_testing_guide.md",
    "developer_guide.md"
)

foreach ($guide in $guides) {
    if (Test-Path "docs\$guide") {
        Move-Item -Path "docs\$guide" -Destination "docs\guides\" -Force
        Write-Host "  Moved: $guide" -ForegroundColor Gray
    }
}

# Archive historical documentation
Write-Host "Moving historical documentation..." -ForegroundColor Yellow
if (Test-Path "docs\file_reorganization.md") {
    Move-Item -Path "docs\file_reorganization.md" -Destination "docs\archive\historical\" -Force
}

# Archive version control updates folder if it exists
if (Test-Path "docs\version_control_updates") {
    Move-Item -Path "docs\version_control_updates" -Destination "docs\archive\historical\" -Force
}

# Clean up redundant README files in tests
Write-Host "Cleaning up redundant README files..." -ForegroundColor Yellow
if (Test-Path "tests\frontend\README.md") {
    $content = Get-Content "tests\frontend\README.md" -Raw
    if ($content.Length -lt 200) {
        Remove-Item -Path "tests\frontend\README.md" -Force
        Write-Host "  Removed minimal frontend test README" -ForegroundColor Gray
    }
}

Write-Host "✅ File reorganization complete!" -ForegroundColor Green
Write-Host "📁 Archive structure created in docs\archive\" -ForegroundColor Cyan
Write-Host "📚 Development guides organized in docs\guides\" -ForegroundColor Cyan
