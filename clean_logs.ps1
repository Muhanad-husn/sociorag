# SocioRAG Log Cleanup Script
# This script cleans up log files to reduce clutter

Write-Host "🧹 Cleaning up SocioRAG log files..." -ForegroundColor Cyan
& ".\scripts\production\app_manager.ps1" -Action clean

Write-Host "`nLog cleanup completed!" -ForegroundColor Green
Write-Host "The system now uses a consolidated logging approach with fewer files."
