# Production Startup Script for SocioRAG
# One-command production launch with comprehensive monitoring

param(
    [switch]$MonitoringOnly,
    [switch]$SkipMonitoring,
    [int]$MonitorDuration = 60
)

Write-Host "🚀 SocioRAG Production Startup" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host ""

# Check if already running
$existingPython = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
if ($existingPython -and -not $MonitoringOnly) {
    Write-Host "⚠️  SocioRAG appears to already be running" -ForegroundColor Yellow
    Write-Host "   Use -MonitoringOnly to start monitoring only, or run .\kill_app_processes.ps1 first" -ForegroundColor Yellow
    exit 1
}

if (-not $MonitoringOnly) {
    # 1. Start Application
    Write-Host "📋 Step 1: Starting SocioRAG Application..." -ForegroundColor Cyan
    .\app_manager.ps1 -Action start -EnableMonitoring -WaitForReady
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to start application" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Application started successfully" -ForegroundColor Green
    Write-Host ""
}

if (-not $SkipMonitoring) {
    # 2. Start Monitoring Dashboard
    Write-Host "📊 Step 2: Launching Monitoring Dashboard..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\monitoring_dashboard.ps1' -RefreshInterval 10 -DetailedMode"
    
    Start-Sleep 2
    Write-Host "✅ Monitoring dashboard launched in separate window" -ForegroundColor Green
    Write-Host ""
    
    # 3. Start Performance Monitoring
    Write-Host "📈 Step 3: Starting Performance Monitor ($MonitorDuration minutes)..." -ForegroundColor Cyan
    Write-Host "   Monitoring with 30-second intervals..." -ForegroundColor Yellow
    .\performance_monitor.ps1 -MonitorDurationMinutes $MonitorDuration -RefreshIntervalSeconds 30
}

Write-Host ""
Write-Host "🎯 Production Environment Ready!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Access Points:" -ForegroundColor White
Write-Host "   • Backend API: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "   • API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "   • Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "   • Health Check: http://127.0.0.1:8000/api/admin/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Management Commands:" -ForegroundColor White
Write-Host "   • Status: .\app_manager.ps1 -Action status" -ForegroundColor Yellow
Write-Host "   • Stop: .\app_manager.ps1 -Action stop" -ForegroundColor Yellow
Write-Host "   • Emergency Stop: .\kill_app_processes.ps1" -ForegroundColor Yellow
Write-Host "   • Load Test: .\load_test.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Log Locations:" -ForegroundColor White
Write-Host "   • Application: .\logs\sociorag.log" -ForegroundColor Gray
Write-Host "   • Errors: .\logs\errors.log" -ForegroundColor Gray
Write-Host "   • Performance: .\logs\performance.log" -ForegroundColor Gray
Write-Host ""

# Quick health check
Write-Host "🔍 Quick Health Check:" -ForegroundColor Magenta
try {
    $healthCheck = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/health" -TimeoutSec 5
    Write-Host "   ✅ API Health: Healthy" -ForegroundColor Green
}
catch {
    Write-Host "   ⚠️  API Health: Not accessible (may still be starting)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 SocioRAG is running in production mode!" -ForegroundColor Green
