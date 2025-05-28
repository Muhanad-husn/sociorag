# SocioRAG Performance Test and Monitoring Script
# This script starts the application, runs performance tests, and monitors system metrics

Write-Host "🔍 SocioRAG Performance Test & Monitoring" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Configuration
$BACKEND_URL = "http://127.0.0.1:8000"
$FRONTEND_URL = "http://localhost:5173"
$TEST_DURATION_MINUTES = 30
$MONITORING_INTERVAL_SECONDS = 10
$LOG_FILE = "logs\performance_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Ensure logs directory exists
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $LOG_FILE -Value $logMessage
}

function Test-ApplicationHealth {
    Write-Log "🏥 Testing Application Health..." "Cyan"
    
    try {
        # Test backend health
        $healthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -Method GET -TimeoutSec 10
        Write-Log "✅ Backend Health: $($healthResponse.status)" "Green"
        
        # Test system metrics
        $metricsResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/metrics" -Method GET -TimeoutSec 10
        Write-Log "📊 CPU Usage: $($metricsResponse.cpu_usage)%" "Yellow"
        Write-Log "💾 Memory Usage: $($metricsResponse.memory_usage.percentage)%" "Yellow"
        Write-Log "💽 Disk Usage: $($metricsResponse.disk_usage.percentage)%" "Yellow"
        
        return $true
    }
    catch {
        Write-Log "❌ Health check failed: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Get-LogAnalytics {
    Write-Log "📈 Fetching Log Analytics..." "Cyan"
    
    try {
        # Get error summary
        $errors = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/errors?hours=1" -Method GET -TimeoutSec 10
        Write-Log "🚨 Error Rate: $($errors.error_rate * 100)%" "Yellow"
        
        # Get performance metrics  
        $performance = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/performance?hours=1" -Method GET -TimeoutSec 10
        if ($performance.api_performance) {
            foreach ($endpoint in $performance.api_performance.PSObject.Properties) {
                $stats = $endpoint.Value
                if ($stats.avg) {
                    Write-Log "⚡ $($endpoint.Name): avg ${stats.avg}ms" "Yellow"
                }
            }
        }
        
        # Get system health from logs
        $health = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/health" -Method GET -TimeoutSec 10
        Write-Log "💚 System Health: $($health.status)" "Green"
        
        return $true
    }
    catch {
        Write-Log "❌ Log analytics failed: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Test-APIEndpoints {
    Write-Log "🔧 Testing Core API Endpoints..." "Cyan"
    
    $endpoints = @(
        @{ Method = "GET"; Uri = "/"; Name = "Root Health Check" },
        @{ Method = "GET"; Uri = "/api/admin/health"; Name = "Admin Health" },
        @{ Method = "GET"; Uri = "/api/admin/metrics"; Name = "System Metrics" },
        @{ Method = "GET"; Uri = "/api/logs/stats"; Name = "Log Statistics" },
        @{ Method = "GET"; Uri = "/api/history/stats"; Name = "History Stats" }
    )
    
    $successCount = 0
    $totalTime = 0
    
    foreach ($endpoint in $endpoints) {
        try {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-RestMethod -Uri "$BACKEND_URL$($endpoint.Uri)" -Method $endpoint.Method -TimeoutSec 5
            $stopwatch.Stop()
            
            $responseTime = $stopwatch.ElapsedMilliseconds
            $totalTime += $responseTime
            $successCount++
            
            Write-Log "✅ $($endpoint.Name): ${responseTime}ms" "Green"
        }
        catch {
            Write-Log "❌ $($endpoint.Name): Failed - $($_.Exception.Message)" "Red"
        }
    }
    
    $avgResponseTime = if ($successCount -gt 0) { [math]::Round($totalTime / $successCount, 2) } else { 0 }
    Write-Log "📊 API Test Summary: $successCount/$($endpoints.Count) successful, Avg: ${avgResponseTime}ms" "Cyan"
    
    return @{ Success = $successCount; Total = $endpoints.Count; AvgTime = $avgResponseTime }
}

function Start-MonitoringLoop {
    param($DurationMinutes)
    
    Write-Log "🔄 Starting monitoring loop for $DurationMinutes minutes..." "Cyan"
    
    $endTime = (Get-Date).AddMinutes($DurationMinutes)
    $iteration = 1
    
    while ((Get-Date) -lt $endTime) {
        Write-Log "--- Monitoring Iteration $iteration ---" "Magenta"
        
        # Test health and collect metrics
        $healthOK = Test-ApplicationHealth
        $analyticsOK = Get-LogAnalytics
        $apiResults = Test-APIEndpoints
        
        # Calculate overall health score
        $healthScore = 0
        if ($healthOK) { $healthScore += 40 }
        if ($analyticsOK) { $healthScore += 30 }
        if ($apiResults.Success -eq $apiResults.Total) { $healthScore += 30 }
        
        Write-Log "🎯 Overall Health Score: $healthScore/100" $(if ($healthScore -ge 80) { "Green" } elseif ($healthScore -ge 60) { "Yellow" } else { "Red" })
        
        Write-Log "⏸️  Waiting $MONITORING_INTERVAL_SECONDS seconds..." "DarkGray"
        Start-Sleep -Seconds $MONITORING_INTERVAL_SECONDS
        $iteration++
    }
}

function Test-DocumentProcessing {
    Write-Log "📄 Testing Document Processing (if test files available)..." "Cyan"
    
    # Check for test files
    if (Test-Path "tests\fixtures\*.pdf") {
        $testFiles = Get-ChildItem "tests\fixtures\*.pdf" | Select-Object -First 1
        Write-Log "📎 Found test file: $($testFiles.Name)" "Yellow"
        
        try {
            # This would require a multipart form upload - for now just note availability
            Write-Log "📋 Document processing test available but requires manual upload" "Yellow"
            Write-Log "💡 Use the frontend at $FRONTEND_URL to test document upload" "Yellow"
        }
        catch {
            Write-Log "❌ Document processing test failed: $($_.Exception.Message)" "Red"
        }
    }
    else {
        Write-Log "📋 No test documents found in tests\fixtures\" "Yellow"
    }
}

# Main execution
Write-Log "🏁 Starting Performance Test and Monitoring" "Green"

# Check if application is already running
Write-Log "🔍 Checking if application is already running..." "Cyan"

try {
    $response = Invoke-WebRequest -Uri "$BACKEND_URL/docs" -TimeoutSec 3 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Log "✅ Application is already running" "Green"
        $appAlreadyRunning = $true
    }
}
catch {
    Write-Log "🔧 Application not running, will need to start it" "Yellow"
    $appAlreadyRunning = $false
}

# Start application if not running
if (-not $appAlreadyRunning) {
    Write-Log "🚀 Starting SocioRAG application..." "Cyan"
    Write-Log "⏳ This may take 15-30 seconds for initial startup..." "Yellow"
    
    # Use the existing quick start script
    if (Test-Path "quick_start.ps1") {
        Start-Process powershell -ArgumentList "-File", "quick_start.ps1" -WindowStyle Hidden
        Start-Sleep -Seconds 20
    }
    else {
        Write-Log "❌ quick_start.ps1 not found. Please start the application manually." "Red"
        exit 1
    }
    
    # Wait for application to be ready
    $attempts = 0
    do {
        try {
            $response = Invoke-WebRequest -Uri "$BACKEND_URL/docs" -TimeoutSec 3 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Log "✅ Application is ready!" "Green"
                break
            }
        }
        catch {
            $attempts++
            if ($attempts -gt 20) {
                Write-Log "❌ Application failed to start within timeout" "Red"
                exit 1
            }
            Write-Log "   Still waiting for startup... (attempt $attempts/20)" "Yellow"
            Start-Sleep -Seconds 3
        }
    } while ($true)
}

# Run initial health check
Write-Log "🔬 Running initial health assessment..." "Cyan"
$initialHealth = Test-ApplicationHealth

if (-not $initialHealth) {
    Write-Log "❌ Initial health check failed. Exiting." "Red"
    exit 1
}

# Test document processing capabilities
Test-DocumentProcessing

# Provide user instructions
Write-Log "" "White"
Write-Log "🎯 PERFORMANCE TEST INSTRUCTIONS" "Green"
Write-Log "=================================" "Green"
Write-Log "🌐 Frontend: $FRONTEND_URL" "Cyan"
Write-Log "🔧 Backend:  $BACKEND_URL" "Cyan"
Write-Log "📚 API Docs: $BACKEND_URL/docs" "Cyan"
Write-Log "" "White"
Write-Log "💡 RECOMMENDED TESTS:" "Yellow"
Write-Log "1. Upload a test PDF document via the frontend" "Yellow"
Write-Log "2. Ask several questions using the Q&A interface" "Yellow"
Write-Log "3. Check the History tab for past queries" "Yellow"
Write-Log "4. Monitor this console for performance metrics" "Yellow"
Write-Log "" "White"

# Ask user if they want to run monitoring
$runMonitoring = Read-Host "Start automated monitoring loop for $TEST_DURATION_MINUTES minutes? (y/n)"

if ($runMonitoring -eq "y" -or $runMonitoring -eq "Y") {
    # Start monitoring loop
    Start-MonitoringLoop -DurationMinutes $TEST_DURATION_MINUTES
    
    Write-Log "✅ Monitoring completed!" "Green"
}
else {
    Write-Log "📊 Manual testing mode. Use the application and check logs manually." "Cyan"
    Write-Log "💡 You can run individual health checks anytime:" "Yellow"
    Write-Log "   - Health: $BACKEND_URL/api/admin/health" "Yellow"
    Write-Log "   - Metrics: $BACKEND_URL/api/admin/metrics" "Yellow"
    Write-Log "   - Logs: $BACKEND_URL/api/logs/stats" "Yellow"
}

# Final summary
Write-Log "" "White"
Write-Log "📋 PERFORMANCE TEST SUMMARY" "Green"
Write-Log "===========================" "Green"
Write-Log "📊 Log file: $LOG_FILE" "Cyan"
Write-Log "🌐 Application URLs:" "Cyan"
Write-Log "   Frontend: $FRONTEND_URL" "White"
Write-Log "   Backend:  $BACKEND_URL" "White"
Write-Log "   API Docs: $BACKEND_URL/docs" "White"
Write-Log "" "White"
Write-Log "✨ Performance testing setup complete!" "Green"

# Keep console open
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
