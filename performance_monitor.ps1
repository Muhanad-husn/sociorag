# SocioRAG Performance Monitor
# Real-time performance monitoring and results compilation

param(
    [int]$MonitorDurationMinutes = 15,
    [int]$RefreshIntervalSeconds = 10
)

$StartTime = Get-Date
$EndTime = $StartTime.AddMinutes($MonitorDurationMinutes)

Write-Host "🔍 SocioRAG Performance Monitor Started" -ForegroundColor Green
Write-Host "⏰ Monitoring Duration: $MonitorDurationMinutes minutes" -ForegroundColor Yellow
Write-Host "🔄 Refresh Interval: $RefreshIntervalSeconds seconds" -ForegroundColor Yellow
Write-Host ""

$IterationCount = 0

while ((Get-Date) -lt $EndTime) {
    $IterationCount++
    $CurrentTime = Get-Date
    $ElapsedTime = $CurrentTime - $StartTime
    $RemainingTime = $EndTime - $CurrentTime
    
    Clear-Host
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🔍 SocioRAG Performance Monitor - Iteration $IterationCount" -ForegroundColor Green
    Write-Host "⏰ Elapsed: $($ElapsedTime.ToString('mm\:ss')) | Remaining: $($RemainingTime.ToString('mm\:ss'))" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Check Backend Health
    try {
        $HealthResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method GET -TimeoutSec 5
        Write-Host "✅ Backend Status: $($HealthResponse.status) - $($HealthResponse.message)" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Backend Status: ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # System Performance
    try {
        $CPU = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples.CookedValue
        $Memory = (Get-WmiObject -Class Win32_OperatingSystem)
        $MemoryUsed = [math]::Round((($Memory.TotalVisibleMemorySize - $Memory.FreePhysicalMemory) / $Memory.TotalVisibleMemorySize) * 100, 1)
        
        Write-Host "📊 CPU Usage: $([math]::Round($CPU, 1))%" -ForegroundColor $(if($CPU -gt 80) { "Red" } elseif($CPU -gt 50) { "Yellow" } else { "Green" })
        Write-Host "🧠 Memory Usage: $MemoryUsed%" -ForegroundColor $(if($MemoryUsed -gt 85) { "Red" } elseif($MemoryUsed -gt 70) { "Yellow" } else { "Green" })
    }
    catch {
        Write-Host "⚠️  Could not retrieve system metrics" -ForegroundColor Yellow
    }
    
    # Check for Running Tests
    $PythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -eq "python"}
    Write-Host ""
    Write-Host "🔬 Active Processes:" -ForegroundColor Cyan
    if ($PythonProcesses) {
        foreach ($proc in $PythonProcesses) {
            $Uptime = (Get-Date) - $proc.StartTime
            Write-Host "  🐍 Python PID $($proc.Id): CPU $([math]::Round($proc.CPU, 2))s, Uptime $($Uptime.ToString('hh\:mm\:ss'))" -ForegroundColor White
        }
    } else {
        Write-Host "  ⚠️  No Python processes detected" -ForegroundColor Yellow
    }
    
    # Check for Test Results
    Write-Host ""
    Write-Host "📋 Recent Test Results:" -ForegroundColor Cyan
    $TestResults = Get-ChildItem -Path "test_results" -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
    if ($TestResults) {
        foreach ($result in $TestResults) {
            Write-Host "  📄 $($result.Name): $($result.LastWriteTime.ToString('HH:mm:ss'))" -ForegroundColor White
        }
    }
    
    $LoadTestResults = Get-ChildItem -Path "logs" -Filter "load_test_results_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 2
    if ($LoadTestResults) {
        foreach ($result in $LoadTestResults) {
            Write-Host "  ⚡ $($result.Name): $($result.LastWriteTime.ToString('HH:mm:ss'))" -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "⏳ Next update in $RefreshIntervalSeconds seconds..." -ForegroundColor Gray
    
    Start-Sleep -Seconds $RefreshIntervalSeconds
}

Write-Host ""
Write-Host "🎯 Performance monitoring completed!" -ForegroundColor Green
Write-Host ""

# Generate summary report
Write-Host "📊 Generating Performance Summary..." -ForegroundColor Cyan

$SummaryFile = "test_results\performance_summary_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

@"
═══════════════════════════════════════════════════════════════
SocioRAG Performance Monitoring Summary
═══════════════════════════════════════════════════════════════

Monitoring Session: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Duration: $MonitorDurationMinutes minutes
Refresh Interval: $RefreshIntervalSeconds seconds
Total Iterations: $IterationCount

System Information:
- OS: $($env:OS)
- Computer: $($env:COMPUTERNAME)
- User: $($env:USERNAME)

Test Results Generated:
"@ | Out-File -FilePath $SummaryFile -Encoding UTF8

# List all test results
Get-ChildItem -Path "test_results" -Filter "*.log" | Sort-Object LastWriteTime -Descending | ForEach-Object {
    "- $($_.Name) ($(($_.LastWriteTime).ToString('yyyy-MM-dd HH:mm:ss')))" | Out-File -FilePath $SummaryFile -Append -Encoding UTF8
}

Get-ChildItem -Path "logs" -Filter "load_test_results_*.json" | Sort-Object LastWriteTime -Descending | ForEach-Object {
    "- $($_.Name) ($(($_.LastWriteTime).ToString('yyyy-MM-dd HH:mm:ss')))" | Out-File -FilePath $SummaryFile -Append -Encoding UTF8
}

Write-Host "📄 Summary saved to: $SummaryFile" -ForegroundColor Green
