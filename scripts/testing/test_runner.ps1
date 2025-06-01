# SocioRAG Comprehensive Test Runner
# Orchestrates performance testing, monitoring, and analysis

param(
    [ValidateSet("quick", "standard", "comprehensive")]
    [string]$TestLevel = "standard",
    [switch]$AutoStart,
    [switch]$GenerateReport,
    [string]$OutputDir = "test_results"
)

# Test configurations
$TestConfigs = @{
    quick = @{
        MonitoringDuration = 5
        LoadTestUsers = 2
        LoadTestDuration = 3
        HealthCheckInterval = 30
        Description = "Quick validation test (5 minutes)"
    }
    standard = @{
        MonitoringDuration = 15
        LoadTestUsers = 3
        LoadTestDuration = 10
        HealthCheckInterval = 60
        Description = "Standard performance test (15 minutes)"
    }
    comprehensive = @{
        MonitoringDuration = 30
        LoadTestUsers = 5
        LoadTestDuration = 20
        HealthCheckInterval = 30
        Description = "Comprehensive stress test (30 minutes)"
    }
}

$Config = $TestConfigs[$TestLevel]
$BACKEND_URL = "http://127.0.0.1:8000"
$FRONTEND_URL = "http://localhost:5173"

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$TestStartTime = Get-Date
$TestId = "sociorag_test_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$TestLogFile = "$OutputDir\$TestId.log"

function Write-TestLog {
    param($Message, $Color = "White", $NoConsole = $false)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    if (-not $NoConsole) {
        Write-Host $logMessage -ForegroundColor $Color
    }
    Add-Content -Path $TestLogFile -Value $logMessage
}

function Write-TestHeader {
    param($Title)
    $separator = "=" * 80
    Write-TestLog $separator "Green"
    Write-TestLog $Title "Green"
    Write-TestLog $separator "Green"
    Write-TestLog ""
}

function Test-Prerequisites {
    Write-TestLog "🔍 Checking prerequisites..." "Cyan"
    
    $prerequisites = @()
    
    # Check if required scripts exist
    $requiredScripts = @(
        "quick_start.ps1",
        "monitoring_dashboard.ps1", 
        "load_test.ps1",
        "performance_test_monitor.ps1"
    )
    
    foreach ($script in $requiredScripts) {
        if (Test-Path $script) {
            Write-TestLog "✅ Found: $script" "Green"
        }
        else {
            Write-TestLog "❌ Missing: $script" "Red"
            $prerequisites += "Missing script: $script"
        }
    }
    
    # Check if data directory exists
    if (Test-Path "data") {
        Write-TestLog "✅ Data directory exists" "Green"
    }
    else {
        Write-TestLog "⚠️  Data directory missing, creating..." "Yellow"
        New-Item -ItemType Directory -Path "data" -Force | Out-Null
    }
    
    # Check for test queries
    if (Test-Path "data\test_queries.txt") {
        Write-TestLog "✅ Test queries file found" "Green"
    }
    else {
        Write-TestLog "⚠️  Test queries file missing, will create default" "Yellow"
    }
    
    return $prerequisites
}

function Start-SocioRAGApplication {
    Write-TestLog "🚀 Starting SocioRAG application using app manager..." "Cyan"
    
    if (Test-Path "app_manager.ps1") {
        try {
            Write-TestLog "📋 Using app_manager.ps1 for coordinated startup..." "Cyan"
            
            # Use the app manager for coordinated startup
            $startArgs = @(
                "-File", "app_manager.ps1",
                "-Action", "start",
                "-WaitForReady",
                "-SkipBrowser",
                "-TimeoutSeconds", "90"
            )
            
            $appManagerProcess = Start-Process powershell -ArgumentList $startArgs -WindowStyle Hidden -PassThru -Wait
            
            if ($appManagerProcess.ExitCode -eq 0) {
                Write-TestLog "✅ Application started successfully via app manager" "Green"
                
                # Verify services are actually running
                Start-Sleep -Seconds 5
                $healthCheck = Test-ServiceHealth
                if ($healthCheck.BackendHealthy -and $healthCheck.FrontendHealthy) {
                    Write-TestLog "✅ Services verified healthy after startup" "Green"
                    return $true
                } else {
                    Write-TestLog "⚠️ Services started but health check failed" "Yellow"
                    return $false
                }
            } else {
                Write-TestLog "❌ App manager startup failed with exit code: $($appManagerProcess.ExitCode)" "Red"
                return $false
            }
        }
        catch {
            Write-TestLog "❌ Error using app manager: $($_.Exception.Message)" "Red"
            Write-TestLog "🔄 Falling back to quick_start.ps1..." "Yellow"
        }
    }
    
    # Fallback to quick_start.ps1
    if (Test-Path "quick_start.ps1") {
        Write-TestLog "🔄 Using quick_start.ps1 as fallback..." "Yellow"
        
        # Start the application
        Start-Process powershell -ArgumentList "-File", "quick_start.ps1" -WindowStyle Hidden
        Write-TestLog "⏳ Waiting for application startup (45 seconds)..." "Yellow"
        Start-Sleep -Seconds 45
        
        # Check if it's running
        $attempts = 0
        $maxAttempts = 12
        while ($attempts -lt $maxAttempts) {
            $healthCheck = Test-ServiceHealth
            if ($healthCheck.BackendHealthy -and $healthCheck.FrontendHealthy) {
                Write-TestLog "✅ SocioRAG started successfully via quick_start!" "Green"
                return $true
            }
            
            $attempts++
            Write-TestLog "   Startup verification $attempts/$maxAttempts..." "Gray"
            Start-Sleep -Seconds 5
        }
        
        Write-TestLog "❌ Application failed to start properly via quick_start.ps1" "Red"
        return $false
    } else {
        Write-TestLog "❌ No startup script found (app_manager.ps1 or quick_start.ps1)" "Red"
        return $false
    }
}

function Test-ServiceHealth {
    $result = @{
        BackendHealthy = $false
        FrontendHealthy = $false
        BackendError = $null
        FrontendError = $null
    }
    
    # Test backend
    try {
        $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -TimeoutSec 10 -ErrorAction Stop
        $result.BackendHealthy = ($response.status -eq "healthy")
    }
    catch {
        $result.BackendError = $_.Exception.Message
    }
    
    # Test frontend
    try {
        $response = Invoke-WebRequest -Uri $FRONTEND_URL -TimeoutSec 10 -ErrorAction Stop
        $result.FrontendHealthy = ($response.StatusCode -eq 200)
    }
    catch {
        $result.FrontendError = $_.Exception.Message
    }
    
    return $result
}

function Start-ApplicationIfNeeded {
    Write-TestLog "🔍 Checking if SocioRAG is running..." "Cyan"
    
    $healthCheck = Test-ServiceHealth
    
    if ($healthCheck.BackendHealthy -and $healthCheck.FrontendHealthy) {
        Write-TestLog "✅ SocioRAG is already running and healthy" "Green"
        return $true
    }
    
    if ($healthCheck.BackendHealthy -and -not $healthCheck.FrontendHealthy) {
        Write-TestLog "⚠️ Backend running but frontend not accessible" "Yellow"
        Write-TestLog "   Backend: ✅ Healthy" "Green"
        Write-TestLog "   Frontend: ❌ $($healthCheck.FrontendError)" "Red"
    }
    elseif (-not $healthCheck.BackendHealthy -and $healthCheck.FrontendHealthy) {
        Write-TestLog "⚠️ Frontend running but backend not accessible" "Yellow"
        Write-TestLog "   Backend: ❌ $($healthCheck.BackendError)" "Red"
        Write-TestLog "   Frontend: ✅ Healthy" "Green"
    }
    else {
        Write-TestLog "🔧 Neither service is running properly" "Yellow"
        Write-TestLog "   Backend: ❌ $($healthCheck.BackendError)" "Red"
        Write-TestLog "   Frontend: ❌ $($healthCheck.FrontendError)" "Red"
    }
    
    if ($AutoStart) {
        Write-TestLog "🚀 Auto-starting SocioRAG..." "Cyan"
        return Start-SocioRAGApplication
    }
    else {
        Write-TestLog "💡 Please start SocioRAG manually and re-run this test" "Yellow"
        Write-TestLog "   Recommended: .\app_manager.ps1 -Action start" "Yellow"
        Write-TestLog "   Alternative: .\quick_start.ps1" "Yellow"
        return $false
    }
}

function Run-BaselineHealthCheck {
    Write-TestLog "🏥 Running baseline health assessment..." "Cyan"
    
    try {
        # System health
        $health = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -TimeoutSec 10
        Write-TestLog "✅ System Health: $($health.status)" "Green"
        
        # System metrics
        $metrics = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/metrics" -TimeoutSec 10
        Write-TestLog "📊 CPU: $($metrics.cpu_usage)%, Memory: $($metrics.memory_usage.percentage)%, Disk: $($metrics.disk_usage.percentage)%" "Yellow"
        
        # Log analytics
        $errors = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/errors?hours=1" -TimeoutSec 10
        Write-TestLog "🚨 Error Rate: $([math]::Round($errors.error_rate * 100, 2))%" "Yellow"
        
        # Component status
        foreach ($component in $health.components.PSObject.Properties) {
            $status = $component.Value.status
            $icon = if ($status -eq "healthy") { "✅" } else { "❌" }
            Write-TestLog "   $icon $($component.Name): $status" $(if ($status -eq "healthy") { "Green" } else { "Red" })
        }
        
        return @{
            Success = $true
            Health = $health
            Metrics = $metrics
            Errors = $errors
        }
    }
    catch {
        Write-TestLog "❌ Baseline health check failed: $($_.Exception.Message)" "Red"
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Start-LoadTest {
    param($Users, $Duration)
    
    Write-TestLog "⚡ Starting load test: $Users users for $Duration minutes..." "Cyan"
    
    if (-not (Test-Path "load_test.ps1")) {
        Write-TestLog "❌ load_test.ps1 not found" "Red"
        return $false
    }
    
    try {
        $loadTestArgs = @(
            "-File", "load_test.ps1",
            "-ConcurrentUsers", $Users,
            "-TestDurationMinutes", $Duration,
            "-RequestDelaySeconds", 3
        )
        
        $loadTestProcess = Start-Process powershell -ArgumentList $loadTestArgs -WindowStyle Hidden -PassThru
        
        Write-TestLog "🔄 Load test started (Process ID: $($loadTestProcess.Id))" "Green"
        Write-TestLog "⏳ Load test will run for $Duration minutes..." "Yellow"
        
        return @{
            Success = $true
            Process = $loadTestProcess
            StartTime = Get-Date
        }
    }
    catch {
        Write-TestLog "❌ Failed to start load test: $($_.Exception.Message)" "Red"
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Monitor-SystemDuringTest {
    param($DurationMinutes, $IntervalSeconds = 30)
    
    Write-TestLog "📊 Starting system monitoring for $DurationMinutes minutes..." "Cyan"
    
    $endTime = (Get-Date).AddMinutes($DurationMinutes)
    $monitoringData = @()
    $iteration = 1
    
    while ((Get-Date) -lt $endTime) {
        try {
            # Collect metrics
            $health = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -TimeoutSec 10
            $metrics = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/metrics" -TimeoutSec 10
            $logs = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/health" -TimeoutSec 10
            
            $dataPoint = @{
                Timestamp = Get-Date
                Iteration = $iteration
                Health = $health.status
                CPU = $metrics.cpu_usage
                Memory = $metrics.memory_usage.percentage
                Disk = $metrics.disk_usage.percentage
                ErrorRate = if ($logs.error_rate) { $logs.error_rate } else { 0 }
                ResponseTime = if ($logs.avg_response_time) { $logs.avg_response_time } else { 0 }
            }
            
            $monitoringData += $dataPoint
            
            Write-TestLog "📊 Monitor [$iteration]: CPU $($dataPoint.CPU)%, Memory $($dataPoint.Memory)%, Health: $($dataPoint.Health)" "Gray"
            
            $iteration++
            Start-Sleep -Seconds $IntervalSeconds
        }
        catch {
            Write-TestLog "⚠️  Monitoring error: $($_.Exception.Message)" "Yellow"
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
    
    Write-TestLog "✅ System monitoring completed ($($monitoringData.Count) data points)" "Green"
    return $monitoringData
}

function Generate-TestReport {
    param($TestResults, $MonitoringData, $BaselineHealth)
    
    Write-TestLog "📝 Generating comprehensive test report..." "Cyan"
    
    $reportFile = "$OutputDir\$TestId"+"_report.html"
    
    $htmlReport = @"
<!DOCTYPE html>
<html>
<head>
    <title>SocioRAG Performance Test Report - $TestId</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; background: #f8f9fa; }
        .metric { display: inline-block; margin: 10px; padding: 10px 15px; background: white; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        .chart { margin: 20px 0; padding: 15px; background: white; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #667eea; color: white; }
        .status-healthy { background-color: #d4edda; color: #155724; }
        .status-warning { background-color: #fff3cd; color: #856404; }
        .status-error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SocioRAG Performance Test Report</h1>
            <p><strong>Test ID:</strong> $TestId</p>
            <p><strong>Test Level:</strong> $TestLevel ($($Config.Description))</p>
            <p><strong>Test Date:</strong> $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
            <p><strong>Duration:</strong> $($Config.MonitoringDuration) minutes</p>
        </div>

        <div class="section">
            <h2>📊 Test Summary</h2>
            <div class="metric">
                <strong>System Health:</strong> 
                <span class="success">✅ $($BaselineHealth.Health.status)</span>
            </div>
            <div class="metric">
                <strong>Test Duration:</strong> $($Config.MonitoringDuration) minutes
            </div>
            <div class="metric">
                <strong>Load Test Users:</strong> $($Config.LoadTestUsers)
            </div>
            <div class="metric">
                <strong>Monitoring Points:</strong> $($MonitoringData.Count)
            </div>
        </div>

        <div class="section">
            <h2>🏥 System Health Status</h2>
            <table>
                <tr><th>Component</th><th>Status</th><th>Details</th></tr>
"@

    # Add component status to report
    if ($BaselineHealth.Health.components) {
        foreach ($component in $BaselineHealth.Health.components.PSObject.Properties) {
            $status = $component.Value.status
            $statusClass = if ($status -eq "healthy") { "status-healthy" } else { "status-error" }
            $details = if ($component.Value.type) { $component.Value.type } else { "N/A" }
            
            $htmlReport += @"
                <tr class="$statusClass">
                    <td>$($component.Name)</td>
                    <td>$status</td>
                    <td>$details</td>
                </tr>
"@
        }
    }

    $htmlReport += @"
            </table>
        </div>

        <div class="section">
            <h2>📈 Performance Metrics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th><th>Status</th></tr>
                <tr>
                    <td>CPU Usage</td>
                    <td>$($BaselineHealth.Metrics.cpu_usage)%</td>
                    <td class="$(if ($BaselineHealth.Metrics.cpu_usage -lt 50) { 'success' } elseif ($BaselineHealth.Metrics.cpu_usage -lt 80) { 'warning' } else { 'error' })">
                        $(if ($BaselineHealth.Metrics.cpu_usage -lt 50) { '✅ Good' } elseif ($BaselineHealth.Metrics.cpu_usage -lt 80) { '⚠️ Moderate' } else { '❌ High' })
                    </td>
                </tr>
                <tr>
                    <td>Memory Usage</td>
                    <td>$($BaselineHealth.Metrics.memory_usage.percentage)%</td>
                    <td class="$(if ($BaselineHealth.Metrics.memory_usage.percentage -lt 60) { 'success' } elseif ($BaselineHealth.Metrics.memory_usage.percentage -lt 80) { 'warning' } else { 'error' })">
                        $(if ($BaselineHealth.Metrics.memory_usage.percentage -lt 60) { '✅ Good' } elseif ($BaselineHealth.Metrics.memory_usage.percentage -lt 80) { '⚠️ Moderate' } else { '❌ High' })
                    </td>
                </tr>
                <tr>
                    <td>Disk Usage</td>
                    <td>$($BaselineHealth.Metrics.disk_usage.percentage)%</td>
                    <td class="$(if ($BaselineHealth.Metrics.disk_usage.percentage -lt 75) { 'success' } elseif ($BaselineHealth.Metrics.disk_usage.percentage -lt 90) { 'warning' } else { 'error' })">
                        $(if ($BaselineHealth.Metrics.disk_usage.percentage -lt 75) { '✅ Good' } elseif ($BaselineHealth.Metrics.disk_usage.percentage -lt 90) { '⚠️ Moderate' } else { '❌ High' })
                    </td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>📊 Monitoring Data Timeline</h2>
            <div class="chart">
                <p><strong>Monitoring Points:</strong> $($MonitoringData.Count) samples over $($Config.MonitoringDuration) minutes</p>
"@

    # Add monitoring data summary
    if ($MonitoringData.Count -gt 0) {
        $avgCpu = [math]::Round(($MonitoringData | Measure-Object -Property CPU -Average).Average, 1)
        $avgMemory = [math]::Round(($MonitoringData | Measure-Object -Property Memory -Average).Average, 1)
        $maxCpu = ($MonitoringData | Measure-Object -Property CPU -Maximum).Maximum
        $maxMemory = ($MonitoringData | Measure-Object -Property Memory -Maximum).Maximum
        
        $htmlReport += @"
                <p><strong>Average CPU:</strong> $avgCpu% | <strong>Peak CPU:</strong> $maxCpu%</p>
                <p><strong>Average Memory:</strong> $avgMemory% | <strong>Peak Memory:</strong> $maxMemory%</p>
                <table>
                    <tr><th>Time</th><th>CPU %</th><th>Memory %</th><th>Health</th></tr>
"@
        
        # Show first 10 monitoring data points
        $sampleData = $MonitoringData | Select-Object -First 10
        foreach ($point in $sampleData) {
            $time = $point.Timestamp.ToString("HH:mm:ss")
            $htmlReport += @"
                    <tr>
                        <td>$time</td>
                        <td>$($point.CPU)%</td>
                        <td>$($point.Memory)%</td>
                        <td>$($point.Health)</td>
                    </tr>
"@
        }
        
        if ($MonitoringData.Count -gt 10) {
            $htmlReport += "<tr><td colspan='4'><em>... and $($MonitoringData.Count - 10) more data points</em></td></tr>"
        }
        
        $htmlReport += "</table>"
    }

    $htmlReport += @"
            </div>
        </div>

        <div class="section">
            <h2>💡 Recommendations</h2>
            <ul>
"@

    # Add recommendations based on performance
    if ($BaselineHealth.Metrics.cpu_usage -gt 80) {
        $htmlReport += "<li class='error'>⚠️ High CPU usage detected. Consider optimizing workload or scaling resources.</li>"
    }
    if ($BaselineHealth.Metrics.memory_usage.percentage -gt 80) {
        $htmlReport += "<li class='error'>⚠️ High memory usage detected. Monitor for memory leaks or consider increasing available memory.</li>"
    }
    if ($BaselineHealth.Metrics.disk_usage.percentage -gt 90) {
        $htmlReport += "<li class='error'>⚠️ Disk space is critically low. Clean up logs and temporary files.</li>"
    }
    if ($BaselineHealth.Errors.error_rate -gt 0.05) {
        $htmlReport += "<li class='warning'>⚠️ Error rate above 5%. Review error logs for issues.</li>"
    }
    
    # Default recommendations
    $htmlReport += @"
                <li class='success'>✅ Continue monitoring system performance during production use.</li>
                <li class='success'>✅ Review log files regularly for any emerging issues.</li>
                <li class='success'>✅ Consider setting up automated monitoring alerts.</li>
                <li class='success'>✅ Test with actual document uploads for complete validation.</li>
            </ul>
        </div>

        <div class="section">
            <h2>📁 Test Artifacts</h2>
            <ul>
                <li><strong>Test Log:</strong> $TestLogFile</li>
                <li><strong>Output Directory:</strong> $OutputDir</li>
                <li><strong>Backend URL:</strong> $BACKEND_URL</li>
                <li><strong>Frontend URL:</strong> $FRONTEND_URL</li>
            </ul>
        </div>

        <div class="section">
            <h2>🔗 Next Steps</h2>
            <ol>
                <li>Review this report for any performance concerns</li>
                <li>Test document upload and Q&A functionality manually</li>
                <li>Monitor the application during real-world usage</li>
                <li>Set up production monitoring and alerting</li>
                <li>Schedule regular performance testing</li>
            </ol>
        </div>

        <footer style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px; text-align: center; color: #666;">
            <p>Report generated on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') by SocioRAG Test Runner</p>
        </footer>
    </div>
</body>
</html>
"@

    try {
        $htmlReport | Out-File -FilePath $reportFile -Encoding UTF8
        Write-TestLog "✅ HTML report generated: $reportFile" "Green"
        
        # Also save raw data as JSON
        $jsonFile = "$OutputDir\$TestId"+"_data.json"
        $testData = @{
            TestId = $TestId
            TestLevel = $TestLevel
            Config = $Config
            StartTime = $TestStartTime
            EndTime = Get-Date
            BaselineHealth = $BaselineHealth
            MonitoringData = $MonitoringData
        }
        $testData | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
        Write-TestLog "💾 Raw data saved: $jsonFile" "Green"
        
        return @{
            HtmlReport = $reportFile
            JsonData = $jsonFile
        }
    }
    catch {
        Write-TestLog "❌ Error generating report: $($_.Exception.Message)" "Red"
        return $null
    }
}

# Main execution
Write-TestHeader "SocioRAG Comprehensive Test Runner - $TestLevel"

Write-TestLog "🔧 Test Configuration:" "Cyan"
Write-TestLog "   Level: $TestLevel" "White"
Write-TestLog "   Description: $($Config.Description)" "White"
Write-TestLog "   Monitoring Duration: $($Config.MonitoringDuration) minutes" "White"
Write-TestLog "   Load Test Users: $($Config.LoadTestUsers)" "White"
Write-TestLog "   Load Test Duration: $($Config.LoadTestDuration) minutes" "White"
Write-TestLog "   Output Directory: $OutputDir" "White"
Write-TestLog ""

# Step 1: Check prerequisites
$prereqIssues = Test-Prerequisites
if ($prereqIssues.Count -gt 0) {
    Write-TestLog "❌ Prerequisites check failed:" "Red"
    foreach ($issue in $prereqIssues) {
        Write-TestLog "   - $issue" "Red"
    }
    exit 1
}
Write-TestLog "✅ Prerequisites check passed" "Green"
Write-TestLog ""

# Step 2: Start application if needed
$appRunning = Start-ApplicationIfNeeded
if (-not $appRunning) {
    Write-TestLog "❌ Cannot proceed without running application" "Red"
    exit 1
}
Write-TestLog ""

# Step 3: Baseline health check
Write-TestHeader "Baseline Health Assessment"
$baselineHealth = Run-BaselineHealthCheck
if (-not $baselineHealth.Success) {
    Write-TestLog "❌ Baseline health check failed, cannot proceed" "Red"
    exit 1
}
Write-TestLog "✅ Baseline health assessment completed" "Green"
Write-TestLog ""

# Step 4: Start load test (if configured)
$loadTestResult = $null
if ($Config.LoadTestUsers -gt 0 -and $Config.LoadTestDuration -gt 0) {
    Write-TestHeader "Load Testing"
    $loadTestResult = Start-LoadTest -Users $Config.LoadTestUsers -Duration $Config.LoadTestDuration
    if ($loadTestResult.Success) {
        Write-TestLog "✅ Load test started successfully" "Green"
    }
    else {
        Write-TestLog "⚠️  Load test failed to start, continuing with monitoring only" "Yellow"
    }
}
Write-TestLog ""

# Step 5: System monitoring
Write-TestHeader "System Monitoring"
$monitoringData = Monitor-SystemDuringTest -DurationMinutes $Config.MonitoringDuration -IntervalSeconds $Config.HealthCheckInterval
Write-TestLog "✅ System monitoring completed" "Green"
Write-TestLog ""

# Step 6: Wait for load test to complete (if running)
if ($loadTestResult -and $loadTestResult.Success) {
    Write-TestLog "⏳ Waiting for load test to complete..." "Yellow"
    try {
        $loadTestResult.Process.WaitForExit()
        Write-TestLog "✅ Load test completed" "Green"
    }
    catch {
        Write-TestLog "⚠️  Load test monitoring error: $($_.Exception.Message)" "Yellow"
    }
}

# Step 7: Generate report
if ($GenerateReport) {
    Write-TestHeader "Report Generation"
    $reportResult = Generate-TestReport -TestResults @{} -MonitoringData $monitoringData -BaselineHealth $baselineHealth
    if ($reportResult) {
        Write-TestLog "✅ Report generation completed" "Green"
        Write-TestLog "📊 HTML Report: $($reportResult.HtmlReport)" "Cyan"
        Write-TestLog "💾 JSON Data: $($reportResult.JsonData)" "Cyan"
    }
}

# Final summary
$testDuration = ((Get-Date) - $TestStartTime).TotalMinutes
Write-TestHeader "Test Completion Summary"
Write-TestLog "🎯 Test Level: $TestLevel" "Green"
Write-TestLog "⏱️  Total Duration: $([math]::Round($testDuration, 1)) minutes" "Green"
Write-TestLog "📊 Monitoring Points: $($monitoringData.Count)" "Green"
Write-TestLog "🏥 Final Health Status: $($baselineHealth.Health.status)" "Green"
Write-TestLog "📁 Test Artifacts:" "Cyan"
Write-TestLog "   - Test Log: $TestLogFile" "White"
Write-TestLog "   - Output Directory: $OutputDir" "White"
if ($reportResult) {
    Write-TestLog "   - HTML Report: $($reportResult.HtmlReport)" "White"
    Write-TestLog "   - JSON Data: $($reportResult.JsonData)" "White"
}
Write-TestLog ""
Write-TestLog "🌐 Application URLs:" "Cyan"
Write-TestLog "   - Frontend: $FRONTEND_URL" "White"
Write-TestLog "   - Backend: $BACKEND_URL" "White"
Write-TestLog "   - API Docs: $BACKEND_URL/docs" "White"
Write-TestLog ""
Write-TestLog "✨ Test run completed successfully!" "Green"

# Open report if generated
if ($reportResult -and $reportResult.HtmlReport) {
    $openReport = Read-Host "Open HTML report in browser? (y/n)"
    if ($openReport -eq "y" -or $openReport -eq "Y") {
        Start-Process $reportResult.HtmlReport
    }
}
