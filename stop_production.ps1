# SocioRAG Production Stop - Convenience Wrapper
# This script redirects to the organized script location

Write-Host "🛑 Stopping SocioRAG Production..." -ForegroundColor Yellow
Write-Host "Redirecting to: scripts\production\stop_production.ps1" -ForegroundColor Yellow

# Execute the actual script
& ".\scripts\production\stop_production.ps1"
