# SocioRAG Production Start - Convenience Wrapper
# This script redirects to the organized script location

param(
    [switch]$EnableMonitoring,
    [switch]$CleanLogs
)

Write-Host "🚀 Starting SocioRAG Production..." -ForegroundColor Green

# Clean logs if requested
if ($CleanLogs) {
    Write-Host "Cleaning up log files before startup..." -ForegroundColor Cyan
    & ".\scripts\production\app_manager.ps1" -Action clean
}

if ($EnableMonitoring) {
    Write-Host "Starting with monitoring enabled" -ForegroundColor Cyan
    & ".\scripts\production\app_manager.ps1" -Action start -WaitForReady -TimeoutSeconds 120 -EnableMonitoring
} else {
    & ".\scripts\production\app_manager.ps1" -Action start -WaitForReady -TimeoutSeconds 120
}

Write-Host "`nNote: SocioRAG now uses a consolidated logging system. View logs in the logs directory." -ForegroundColor Cyan
Write-Host "      Main application log: logs\sociorag_application.log" -ForegroundColor Cyan
