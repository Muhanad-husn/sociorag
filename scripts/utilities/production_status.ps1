# Production Status Checker for SocioRAG
# Quick status overview for production environment

Write-Host "📊 SocioRAG Production Status Check" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Check if processes are running
Write-Host "🔍 Process Status:" -ForegroundColor Cyan
$pythonProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue

if ($pythonProcess) {
    $uptimeMinutes = [math]::Round((Get-Date - $pythonProcess.StartTime).TotalMinutes, 1)
    Write-Host "   ✅ Backend: Running (Uptime: $uptimeMinutes minutes)" -ForegroundColor Green
    Write-Host "      PID: $($pythonProcess.Id), Memory: $([math]::Round($pythonProcess.WorkingSet / 1MB, 1))MB" -ForegroundColor Gray
} else {
    Write-Host "   ❌ Backend: Not running" -ForegroundColor Red
}

if ($nodeProcess) {
    Write-Host "   ✅ Frontend: Running" -ForegroundColor Green
    Write-Host "      PID: $($nodeProcess.Id), Memory: $([math]::Round($nodeProcess.WorkingSet / 1MB, 1))MB" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Frontend: Not running" -ForegroundColor Yellow
}

Write-Host ""

# API Health Check
Write-Host "🏥 API Health Check:" -ForegroundColor Cyan
try {
    $startTime = Get-Date
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/health" -TimeoutSec 10
    $responseTime = [math]::Round(((Get-Date) - $startTime).TotalMilliseconds, 2)
    
    Write-Host "   ✅ API: Healthy (Response: ${responseTime}ms)" -ForegroundColor Green
    if ($health.status) {
        Write-Host "      Status: $($health.status)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ API: Unhealthy or unreachable" -ForegroundColor Red
    Write-Host "      Error: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host ""

# System Resources
Write-Host "💻 System Resources:" -ForegroundColor Cyan
try {
    $cpu = [math]::Round((Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples.CookedValue, 1)
    $memory = [math]::Round((Get-Counter "\Memory\Available MBytes").CounterSamples.CookedValue, 0)
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'" | ForEach-Object { [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 1) }
    
    $cpuColor = if ($cpu -gt 80) { "Red" } elseif ($cpu -gt 60) { "Yellow" } else { "Green" }
    $memColor = if ($memory -lt 1000) { "Red" } elseif ($memory -lt 2000) { "Yellow" } else { "Green" }
    $diskColor = if ($disk -gt 90) { "Red" } elseif ($disk -gt 80) { "Yellow" } else { "Green" }
    
    Write-Host "   CPU Usage: $cpu%" -ForegroundColor $cpuColor
    Write-Host "   Available Memory: ${memory}MB" -ForegroundColor $memColor
    Write-Host "   Disk Usage: $disk%" -ForegroundColor $diskColor
} catch {
    Write-Host "   ⚠️  Could not retrieve system metrics" -ForegroundColor Yellow
}

Write-Host ""

# Recent Logs Check
Write-Host "📋 Recent Log Activity:" -ForegroundColor Cyan
$logFiles = @(
    @{Path=".\logs\sociorag.log"; Name="Application"},
    @{Path=".\logs\errors.log"; Name="Errors"},
    @{Path=".\logs\performance.log"; Name="Performance"}
)

foreach ($log in $logFiles) {
    if (Test-Path $log.Path) {
        $recentLines = Get-Content $log.Path -Tail 1 -ErrorAction SilentlyContinue
        if ($recentLines) {
            $lastActivity = "Recent activity"
        } else {
            $lastActivity = "No recent activity"
        }
        Write-Host "   📄 $($log.Name): $lastActivity" -ForegroundColor Gray
    } else {
        Write-Host "   📄 $($log.Name): No log file" -ForegroundColor Yellow
    }
}

Write-Host ""

# Quick Test
Write-Host "🧪 Quick Functionality Test:" -ForegroundColor Cyan
try {
    $testResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -TimeoutSec 5
    if ($testResponse) {
        Write-Host "   ✅ Root endpoint: Responding" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Root endpoint: Not responding" -ForegroundColor Red
}

Write-Host ""

# Access Information
Write-Host "🔗 Access Points:" -ForegroundColor Magenta
Write-Host "   • Backend API: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "   • API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "   • Health Check: http://127.0.0.1:8000/api/admin/health" -ForegroundColor Cyan
if ($nodeProcess) {
    Write-Host "   • Frontend UI: http://localhost:5173" -ForegroundColor Cyan
}

Write-Host ""

# Management Commands
Write-Host "🔧 Management Commands:" -ForegroundColor Magenta
Write-Host "   • Start monitoring: .\monitoring_dashboard.ps1" -ForegroundColor Yellow
Write-Host "   • Performance test: .\load_test.ps1" -ForegroundColor Yellow
Write-Host "   • Stop services: .\app_manager.ps1 -Action stop" -ForegroundColor Yellow
Write-Host "   • Emergency stop: .\kill_app_processes.ps1" -ForegroundColor Yellow

Write-Host ""

# Summary
if ($pythonProcess -and (try { Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -TimeoutSec 3; $true } catch { $false })) {
    Write-Host "🎯 Overall Status: ✅ PRODUCTION READY" -ForegroundColor Green
} elseif ($pythonProcess) {
    Write-Host "🎯 Overall Status: ⚠️  PARTIALLY RUNNING" -ForegroundColor Yellow
} else {
    Write-Host "🎯 Overall Status: ❌ NOT RUNNING" -ForegroundColor Red
    Write-Host "   Run: .\production_start.ps1 to start" -ForegroundColor Yellow
}

Write-Host ""
