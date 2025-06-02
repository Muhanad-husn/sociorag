# SocioRAG Production Stop - Convenience Wrapper
# This script redirects to the organized script location

Write-Host "🛑 Stopping SocioRAG Production..." -ForegroundColor Yellow
Write-Host "Redirecting to: scripts\production\app_manager.ps1 -Action stop" -ForegroundColor Yellow

# Execute the actual script
& ".\scripts\production\app_manager.ps1" -Action stop
