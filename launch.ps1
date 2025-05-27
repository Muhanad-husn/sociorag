#!/usr/bin/env pwsh
# Quick launcher for SocioRAG - starts both backend and frontend
# Usage: .\launch.ps1

# Set colors
$Host.UI.RawUI.ForegroundColor = "Cyan"

Clear-Host
Write-Host "🚀 SocioRAG Quick Launcher" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend\app\main.py")) {
    Write-Host "❌ Error: Please run this from the SocioRAG root directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting SocioRAG application..." -ForegroundColor Yellow
Write-Host ""

# Run the full startup script
try {
    & ".\start_app.ps1"
}
catch {
    Write-Host "❌ Failed to start application: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try running manually:" -ForegroundColor Yellow
    Write-Host "  1. .\start_app.ps1" -ForegroundColor White
    Write-Host "  2. Or see STARTUP_GUIDE.md for troubleshooting" -ForegroundColor White
    Read-Host "Press Enter to exit"
}
