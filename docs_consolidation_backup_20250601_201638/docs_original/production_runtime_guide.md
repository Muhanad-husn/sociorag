# SocioRAG Production Runtime Guide

## 🚀 INSTANT PRODUCTION START

### One-Command Launch
```powershell
# Start SocioRAG in production mode with monitoring
.\production_start.ps1
```

### Quick Status Check
```powershell
# Check if everything is running properly
.\production_status.ps1
```

### Essential Commands
```powershell
# Start monitoring dashboard
.\monitoring_dashboard.ps1 -DetailedMode

# Run performance test
.\load_test.ps1 -ConcurrentUsers 3 -TestDurationMinutes 5

# Emergency stop
.\kill_app_processes.ps1
```

### ✅ Access Points (Once Running)
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs  
- **Health Check**: http://127.0.0.1:8000/api/admin/health
- **Frontend UI**: http://localhost:5173

---

## Overview

This guide provides simplified instructions to run your existing SocioRAG repository in a production or real work environment with performance monitoring and error tracking.

## 🚀 Quick Production Start

### Prerequisites Check
```powershell
# Verify you have the requirements
python --version          # Should be 3.12+
node --version            # Should be 18+
docker --version          # Optional but recommended
```

### 1. Environment Setup

Create production configuration:
```powershell
# Copy and configure environment
Copy-Item "config.yaml.example" "config.yaml"
```

Edit `config.yaml` with your production settings:
```yaml
# Production Configuration
environment: "production"
debug: false
log_level: "INFO"

# API Configuration
openrouter_api_key: "your-production-api-key"
api_host: "0.0.0.0"
api_port: 8000

# Database Paths
graph_db_path: "./data/graph.db"
vector_store_path: "./vector_store"

# Performance Settings
chunk_similarity_threshold: 0.85
entity_similarity_threshold: 0.90
top_k_results: 100
top_k_rerank: 15
max_context_fraction: 0.4

# Monitoring
enable_metrics: true
log_performance: true
log_file: "./logs/sociorag.log"
error_log_file: "./logs/errors.log"
```

### 2. Install Dependencies

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies (if running UI)
cd ui
npm install
cd ..
```

### 3. Start Production Services

**Option A: Full Stack (Recommended)**
```powershell
# Start with monitoring
.\monitoring_dashboard.ps1 -Environment production -EnableAlerts
```

**Option B: Backend Only**
```powershell
# Start backend with production config
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

**Option C: Using Docker (Recommended for isolation)**
```powershell
# Build and run with Docker
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Performance Monitoring Setup

### 1. Real-time Performance Monitor

The repository includes a built-in performance monitor. Start it:

```powershell
# Start performance monitoring
.\performance_monitor.ps1 -Environment production -AlertThreshold 80 -CheckInterval 30
```

This will monitor:
- **CPU Usage**: Alert if >80%
- **Memory Usage**: Alert if >85%
- **Response Times**: Alert if >2 seconds
- **Error Rate**: Alert if >1%
- **Disk Usage**: Alert if >80%

### 2. Application Health Monitoring

Start the application health monitor:

```powershell
# Monitor application health
.\app_manager.ps1 -Mode monitor -Environment production
```

This monitors:
- API endpoint availability
- Database connections
- Vector store health
- Model loading status
- Memory leaks

### 3. Custom Monitoring Dashboard

Create a monitoring dashboard:

```powershell
# Start monitoring dashboard
.\monitoring_dashboard.ps1 -Port 3001 -EnableRealtime
```

Access at: `http://localhost:3001`

## 🚨 Error Tracking and Debugging

### 1. Real-time Error Monitoring

The system automatically logs errors to:
- `./logs/errors.log` - Application errors
- `./logs/sociorag.log` - General application logs
- `./logs/performance.log` - Performance metrics

### 2. Error Alert System

Create an error monitoring script:

```powershell
# Monitor for errors in real-time
Get-Content "./logs/errors.log" -Wait | Where-Object { $_ -match "ERROR|CRITICAL" } | ForEach-Object {
    Write-Host "🚨 ERROR DETECTED: $_" -ForegroundColor Red
    # Add notification logic here (email, Slack, etc.)
}
```

### 3. Performance Bottleneck Detection

Monitor for performance issues:

```powershell
# Watch for slow queries
Get-Content "./logs/performance.log" -Wait | Where-Object { 
    $_ -match "response_time" -and ([regex]::Match($_, "(\d+\.?\d*)").Value -as [double]) -gt 2.0 
} | ForEach-Object {
    Write-Host "⚠️ SLOW RESPONSE: $_" -ForegroundColor Yellow
}
```

## 🔧 Production Configuration Optimization

### 1. Performance Tuning

For high-load environments, update `config.yaml`:

```yaml
# High Performance Settings
max_concurrent_requests: 50
request_timeout: 300
cache_size: 1000
batch_size: 100

# Memory Management
max_memory_usage: "4GB"
garbage_collection_threshold: 0.7

# Database Optimization
db_connection_pool_size: 20
vector_store_cache_size: 500MB
```

### 2. Resource Limits

Set resource limits in your environment:

```powershell
# Set process priority
$process = Get-Process -Name "python" | Where-Object { $_.MainWindowTitle -like "*sociorag*" }
$process.PriorityClass = "High"

# Monitor resource usage
while ($true) {
    $cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples.CookedValue
    $memory = (Get-Process -Name "python" | Measure-Object WorkingSet -Sum).Sum / 1GB
    
    Write-Host "CPU: $([math]::Round($cpu, 2))% | Memory: $([math]::Round($memory, 2))GB" -ForegroundColor Cyan
    Start-Sleep 30
}
```

## 📈 Performance Metrics Dashboard

### 1. Key Metrics to Track

Create a metrics collection script:

```powershell
# performance_metrics.ps1
param(
    [int]$IntervalSeconds = 60,
    [string]$LogFile = "./logs/metrics.json"
)

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    
    # System Metrics
    $cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples.CookedValue
    $memory = (Get-Counter "\Memory\Available MBytes").CounterSamples.CookedValue
    $disk = (Get-Counter "\LogicalDisk(_Total)\% Free Space").CounterSamples.CookedValue
    
    # Application Metrics (if API is running)
    try {
        $healthCheck = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/health" -TimeoutSec 5
        $apiStatus = "healthy"
        $responseTime = (Measure-Command { Invoke-RestMethod -Uri "http://localhost:8000/api/admin/health" }).TotalMilliseconds
    }
    catch {
        $apiStatus = "unhealthy"
        $responseTime = -1
    }
    
    # Create metrics object
    $metrics = @{
        timestamp = $timestamp
        system = @{
            cpu_usage = [math]::Round($cpu, 2)
            memory_available_mb = [math]::Round($memory, 2)
            disk_free_percent = [math]::Round($disk, 2)
        }
        application = @{
            status = $apiStatus
            response_time_ms = $responseTime
        }
    }
    
    # Log metrics
    $metrics | ConvertTo-Json -Compress | Add-Content $LogFile
    
    # Console output
    Write-Host "[$timestamp] CPU: $($metrics.system.cpu_usage)% | Memory: $($metrics.system.memory_available_mb)MB | API: $($metrics.application.status)" -ForegroundColor Green
    
    Start-Sleep $IntervalSeconds
}
```

### 2. Automated Performance Reports

Create daily performance reports:

```powershell
# daily_performance_report.ps1
$today = Get-Date -Format "yyyy-MM-dd"
$logFile = "./logs/metrics.json"
$reportFile = "./logs/performance_report_$today.txt"

# Analyze metrics from today
$todayMetrics = Get-Content $logFile | Where-Object { $_ -like "*$today*" } | ConvertFrom-Json

if ($todayMetrics.Count -gt 0) {
    $avgCpu = ($todayMetrics | Measure-Object -Property "system.cpu_usage" -Average).Average
    $avgMemory = ($todayMetrics | Measure-Object -Property "system.memory_available_mb" -Average).Average
    $apiUptime = ($todayMetrics | Where-Object { $_.application.status -eq "healthy" }).Count / $todayMetrics.Count * 100
    
    $report = @"
# SocioRAG Performance Report - $today

## System Performance
- Average CPU Usage: $([math]::Round($avgCpu, 2))%
- Average Available Memory: $([math]::Round($avgMemory, 2))MB
- API Uptime: $([math]::Round($apiUptime, 2))%

## Alerts Generated
$(Get-Content "./logs/errors.log" | Where-Object { $_ -like "*$today*" } | Measure-Object | Select-Object -ExpandProperty Count) errors logged

## Recommendations
$(if ($avgCpu -gt 80) { "⚠️ High CPU usage detected - consider scaling" })
$(if ($avgMemory -lt 1000) { "⚠️ Low memory available - monitor for memory leaks" })
$(if ($apiUptime -lt 99) { "🚨 API uptime below 99% - investigate issues" })
"@

    $report | Out-File $reportFile
    Write-Host "Performance report generated: $reportFile" -ForegroundColor Green
}
```

## 🔍 Debugging and Troubleshooting

### 1. Common Issues and Solutions

**High CPU Usage:**
```powershell
# Check for runaway processes
Get-Process -Name "python" | Select-Object Name, CPU, WorkingSet | Sort-Object CPU -Descending

# Reduce concurrent requests
# Edit config.yaml: max_concurrent_requests: 25
```

**Memory Leaks:**
```powershell
# Monitor memory growth over time
$memoryUsage = @()
for ($i = 0; $i -lt 60; $i++) {
    $memory = (Get-Process -Name "python" | Measure-Object WorkingSet -Sum).Sum / 1MB
    $memoryUsage += $memory
    Write-Host "Memory: $([math]::Round($memory, 2))MB"
    Start-Sleep 60
}

# Check for growth trend
$trend = $memoryUsage[-1] - $memoryUsage[0]
if ($trend -gt 100) { Write-Host "⚠️ Memory leak detected: +$([math]::Round($trend, 2))MB in 1 hour" -ForegroundColor Yellow }
```

**Slow Response Times:**
```powershell
# Test API response times
$endpoints = @(
    "http://localhost:8000/api/admin/health",
    "http://localhost:8000/api/v1/status"
)

foreach ($endpoint in $endpoints) {
    $responseTime = (Measure-Command { 
        try { Invoke-RestMethod -Uri $endpoint -TimeoutSec 10 }
        catch { Write-Host "Failed to reach $endpoint" }
    }).TotalMilliseconds
    
    Write-Host "$endpoint : $([math]::Round($responseTime, 2))ms" -ForegroundColor $(if ($responseTime -gt 2000) { "Red" } else { "Green" })
}
```

### 2. Log Analysis Tools

Create log analysis helpers:

```powershell
# analyze_logs.ps1
param(
    [string]$LogType = "error",
    [int]$LastHours = 24
)

$cutoffTime = (Get-Date).AddHours(-$LastHours)
$logFile = switch ($LogType) {
    "error" { "./logs/errors.log" }
    "performance" { "./logs/performance.log" }
    default { "./logs/sociorag.log" }
}

Get-Content $logFile | Where-Object {
    $logTime = [DateTime]::ParseExact(($_ -split " ")[0] + " " + ($_ -split " ")[1], "yyyy-MM-dd HH:mm:ss", $null)
    $logTime -gt $cutoffTime
} | Group-Object { ($_ -split " ")[2] } | Sort-Object Count -Descending | Format-Table Name, Count
```

## 🎯 Production Deployment Commands

### Complete Production Startup

Create a single production startup script:

```powershell
# production_start.ps1
Write-Host "🚀 Starting SocioRAG in Production Mode..." -ForegroundColor Green

# 1. Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Cyan
python --version
node --version

# 2. Start backend
Write-Host "🔧 Starting backend services..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 2" -WindowStyle Normal

# 3. Start monitoring
Write-Host "📊 Starting monitoring..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList ".\performance_metrics.ps1" -WindowStyle Normal

# 4. Start frontend (optional)
$frontendChoice = Read-Host "Start frontend? (y/n)"
if ($frontendChoice -eq "y") {
    Write-Host "🎨 Starting frontend..." -ForegroundColor Cyan
    Set-Location ui
    Start-Process powershell -ArgumentList "npm run dev" -WindowStyle Normal
    Set-Location ..
}

# 5. Health check
Write-Host "🔍 Performing health check..." -ForegroundColor Cyan
Start-Sleep 10
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/health"
    Write-Host "✅ SocioRAG is running successfully!" -ForegroundColor Green
    Write-Host "📊 Dashboard: http://localhost:3001" -ForegroundColor Yellow
    Write-Host "🔗 API: http://localhost:8000" -ForegroundColor Yellow
}
catch {
    Write-Host "❌ Failed to start - check logs for errors" -ForegroundColor Red
}
```

### Quick Status Check

```powershell
# status_check.ps1
Write-Host "📊 SocioRAG Production Status" -ForegroundColor Green
Write-Host "=" * 40

# Check processes
$pythonProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
$nodeProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue

Write-Host "Backend: $(if ($pythonProcess) { '✅ Running' } else { '❌ Stopped' })"
Write-Host "Frontend: $(if ($nodeProcess) { '✅ Running' } else { '❌ Stopped' })"

# Check API health
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/health" -TimeoutSec 5
    Write-Host "API Health: ✅ Healthy"
    Write-Host "Response Time: $((Measure-Command { Invoke-RestMethod -Uri "http://localhost:8000/api/admin/health" }).TotalMilliseconds)ms"
}
catch {
    Write-Host "API Health: ❌ Unhealthy"
}

# Resource usage
$cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples.CookedValue
$memory = (Get-Counter "\Memory\Available MBytes").CounterSamples.CookedValue
Write-Host "CPU Usage: $([math]::Round($cpu, 1))%"
Write-Host "Available Memory: $([math]::Round($memory, 0))MB"
```

## 📋 Production Checklist

### Before Starting
- [ ] Update `config.yaml` with production settings
- [ ] Ensure OpenRouter API key is configured
- [ ] Check available disk space (>5GB recommended)
- [ ] Verify network connectivity
- [ ] Close unnecessary applications

### During Operation
- [ ] Monitor CPU usage (<80%)
- [ ] Monitor memory usage (<85%)
- [ ] Check response times (<2s)
- [ ] Monitor error logs
- [ ] Verify API health every 30 minutes

### Daily Tasks
- [ ] Check performance reports
- [ ] Review error logs
- [ ] Backup data directory
- [ ] Monitor disk space
- [ ] Restart if memory usage is high

---

## 🆘 Emergency Procedures

### Service Recovery
```powershell
# emergency_restart.ps1
Write-Host "🚨 Emergency restart procedure..." -ForegroundColor Red

# Stop all processes
Get-Process -Name "python" | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force
Get-Process -Name "node" | Stop-Process -Force

# Wait and restart
Start-Sleep 5
.\production_start.ps1
```

### Performance Issues
```powershell
# performance_emergency.ps1
Write-Host "⚡ Performance optimization..." -ForegroundColor Yellow

# Clear cache
Remove-Item "./vector_store/cache/*" -Force -ErrorAction SilentlyContinue

# Restart with reduced load
$env:MAX_CONCURRENT_REQUESTS = "25"
$env:BATCH_SIZE = "50"

# Restart services
.\emergency_restart.ps1
```

This guide provides everything you need to run SocioRAG in production with comprehensive monitoring and error tracking. Start with the production startup script and use the monitoring tools to ensure optimal performance.
