# SocioRAG Production Start - Convenience Wrapper
# This script redirects to the organized script location

param(
    [switch]$EnableMonitoring
)

Write-Host "🚀 Starting SocioRAG Production..." -ForegroundColor Green

if ($EnableMonitoring) {
    Write-Host "Starting with monitoring enabled" -ForegroundColor Cyan
    & ".\scripts\production\app_manager.ps1" -Action start -WaitForReady -TimeoutSeconds 120 -EnableMonitoring
} else {
    & ".\scripts\production\app_manager.ps1" -Action start -WaitForReady -TimeoutSeconds 120
}
