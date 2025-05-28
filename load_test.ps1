# SocioRAG Load Testing Script
# Simulates realistic user interactions to test performance under load

param(
    [int]$ConcurrentUsers = 3,
    [int]$TestDurationMinutes = 10,
    [int]$RequestDelaySeconds = 2,
    [string]$TestQueries = "data/test_queries.txt"
)

# Configuration
$BACKEND_URL = "http://127.0.0.1:8000"
$RESULTS_FILE = "logs\load_test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$LOG_FILE = "logs\load_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Ensure logs directory exists
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Default test queries if file doesn't exist
$DefaultQueries = @(
    "What are the main themes in the document?",
    "Can you summarize the key findings?",
    "What methodology was used in this research?",
    "What are the conclusions and recommendations?",
    "Who are the main authors or contributors mentioned?",
    "What data sources were referenced?",
    "What are the limitations of this study?",
    "What future research directions are suggested?",
    "What is the significance of these findings?",
    "How does this relate to previous work in the field?"
)

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $LOG_FILE -Value $logMessage
}

function Get-TestQueries {
    if (Test-Path $TestQueries) {
        try {
            $queries = Get-Content $TestQueries | Where-Object { $_.Trim() -ne "" }
            Write-Log "📋 Loaded $($queries.Count) test queries from $TestQueries" "Green"
            return $queries
        }
        catch {
            Write-Log "⚠️  Error reading test queries file, using defaults" "Yellow"
            return $DefaultQueries
        }
    }
    else {
        Write-Log "📋 Using default test queries (file not found: $TestQueries)" "Yellow"
        return $DefaultQueries
    }
}

function Test-APIEndpoint {
    param($Method, $Uri, $Body = $null, $TimeoutSec = 30)
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        $params = @{
            Uri = "$BACKEND_URL$Uri"
            Method = $Method
            TimeoutSec = $TimeoutSec
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        $stopwatch.Stop()
        
        return @{
            Success = $true
            ResponseTime = $stopwatch.ElapsedMilliseconds
            StatusCode = 200
            Response = $response
        }
    }
    catch {
        $stopwatch.Stop()
        return @{
            Success = $false
            ResponseTime = $stopwatch.ElapsedMilliseconds
            Error = $_.Exception.Message
            StatusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode } else { "Unknown" }
        }
    }
}

function Start-UserSimulation {
    param($UserId, $Queries, $TestDurationMinutes, $DelaySeconds)
    
    $endTime = (Get-Date).AddMinutes($TestDurationMinutes)
    $userResults = @{
        UserId = $UserId
        TotalRequests = 0
        SuccessfulRequests = 0
        FailedRequests = 0
        TotalResponseTime = 0
        MinResponseTime = [int]::MaxValue
        MaxResponseTime = 0
        Errors = @()
        StartTime = Get-Date
    }
    
    Write-Log "👤 User $UserId started simulation" "Cyan"
    
    while ((Get-Date) -lt $endTime) {
        # Random query selection
        $query = $Queries | Get-Random
        
        # Test health check
        $healthResult = Test-APIEndpoint -Method "GET" -Uri "/api/admin/health" -TimeoutSec 10
        $userResults.TotalRequests++
        
        if ($healthResult.Success) {
            $userResults.SuccessfulRequests++
            $userResults.TotalResponseTime += $healthResult.ResponseTime
            $userResults.MinResponseTime = [math]::Min($userResults.MinResponseTime, $healthResult.ResponseTime)
            $userResults.MaxResponseTime = [math]::Max($userResults.MaxResponseTime, $healthResult.ResponseTime)
        }
        else {
            $userResults.FailedRequests++
            $userResults.Errors += @{
                Timestamp = Get-Date
                Endpoint = "/api/admin/health"
                Error = $healthResult.Error
            }
            Write-Log "❌ User $UserId: Health check failed - $($healthResult.Error)" "Red"
        }
        
        # Test Q&A endpoint (if documents are loaded)
        $qaBody = @{
            query = $query
            language = "en"
        }
        
        $qaResult = Test-APIEndpoint -Method "POST" -Uri "/api/qa/ask" -Body $qaBody -TimeoutSec 30
        $userResults.TotalRequests++
        
        if ($qaResult.Success) {
            $userResults.SuccessfulRequests++
            $userResults.TotalResponseTime += $qaResult.ResponseTime
            $userResults.MinResponseTime = [math]::Min($userResults.MinResponseTime, $qaResult.ResponseTime)
            $userResults.MaxResponseTime = [math]::Max($userResults.MaxResponseTime, $qaResult.ResponseTime)
            Write-Log "✅ User $UserId: Q&A request completed in $($qaResult.ResponseTime)ms" "Green"
        }
        else {
            $userResults.FailedRequests++
            $userResults.Errors += @{
                Timestamp = Get-Date
                Endpoint = "/api/qa/ask"
                Query = $query
                Error = $qaResult.Error
            }
            Write-Log "❌ User $UserId: Q&A request failed - $($qaResult.Error)" "Red"
        }
        
        # Test metrics endpoint
        $metricsResult = Test-APIEndpoint -Method "GET" -Uri "/api/admin/metrics" -TimeoutSec 10
        $userResults.TotalRequests++
        
        if ($metricsResult.Success) {
            $userResults.SuccessfulRequests++
            $userResults.TotalResponseTime += $metricsResult.ResponseTime
            $userResults.MinResponseTime = [math]::Min($userResults.MinResponseTime, $metricsResult.ResponseTime)
            $userResults.MaxResponseTime = [math]::Max($userResults.MaxResponseTime, $metricsResult.ResponseTime)
        }
        else {
            $userResults.FailedRequests++
            $userResults.Errors += @{
                Timestamp = Get-Date
                Endpoint = "/api/admin/metrics"
                Error = $metricsResult.Error
            }
        }
        
        # Wait between requests
        Start-Sleep -Seconds $DelaySeconds
    }
    
    $userResults.EndTime = Get-Date
    $userResults.TestDuration = ($userResults.EndTime - $userResults.StartTime).TotalMinutes
    $userResults.AverageResponseTime = if ($userResults.SuccessfulRequests -gt 0) { 
        [math]::Round($userResults.TotalResponseTime / $userResults.SuccessfulRequests, 2) 
    } else { 0 }
    $userResults.SuccessRate = if ($userResults.TotalRequests -gt 0) { 
        [math]::Round(($userResults.SuccessfulRequests / $userResults.TotalRequests) * 100, 2) 
    } else { 0 }
    
    Write-Log "🏁 User $UserId completed: $($userResults.TotalRequests) requests, $($userResults.SuccessRate)% success rate" "Cyan"
    
    return $userResults
}

function Show-LoadTestSummary {
    param($Results)
    
    Write-Log "" "White"
    Write-Log "📊 LOAD TEST SUMMARY" "Green"
    Write-Log "====================" "Green"
    
    $totalRequests = ($Results | Measure-Object -Property TotalRequests -Sum).Sum
    $totalSuccessful = ($Results | Measure-Object -Property SuccessfulRequests -Sum).Sum
    $totalFailed = ($Results | Measure-Object -Property FailedRequests -Sum).Sum
    $overallSuccessRate = if ($totalRequests -gt 0) { [math]::Round(($totalSuccessful / $totalRequests) * 100, 2) } else { 0 }
    
    $avgResponseTimes = $Results | Where-Object { $_.SuccessfulRequests -gt 0 } | ForEach-Object { $_.AverageResponseTime }
    $overallAvgResponseTime = if ($avgResponseTimes.Count -gt 0) { [math]::Round(($avgResponseTimes | Measure-Object -Average).Average, 2) } else { 0 }
    
    $minResponseTime = ($Results | Where-Object { $_.MinResponseTime -ne [int]::MaxValue } | Measure-Object -Property MinResponseTime -Minimum).Minimum
    $maxResponseTime = ($Results | Measure-Object -Property MaxResponseTime -Maximum).Maximum
    
    Write-Log "👥 Concurrent Users: $ConcurrentUsers" "Cyan"
    Write-Log "⏱️  Test Duration: $TestDurationMinutes minutes" "Cyan"
    Write-Log "📊 Total Requests: $totalRequests" "White"
    Write-Log "✅ Successful: $totalSuccessful" "Green"
    Write-Log "❌ Failed: $totalFailed" "Red"
    Write-Log "📈 Success Rate: $overallSuccessRate%" $(if ($overallSuccessRate -ge 95) { "Green" } elseif ($overallSuccessRate -ge 80) { "Yellow" } else { "Red" })
    Write-Log "⚡ Average Response Time: ${overallAvgResponseTime}ms" "White"
    Write-Log "🚀 Fastest Response: ${minResponseTime}ms" "Green"
    Write-Log "🐌 Slowest Response: ${maxResponseTime}ms" "Yellow"
    
    # Per-user breakdown
    Write-Log "" "White"
    Write-Log "👤 PER-USER RESULTS:" "Cyan"
    foreach ($result in $Results) {
        Write-Log "   User $($result.UserId): $($result.TotalRequests) req, $($result.SuccessRate)% success, ${result.AverageResponseTime}ms avg" "White"
    }
    
    # Error summary
    $allErrors = $Results | ForEach-Object { $_.Errors } | Where-Object { $_ }
    if ($allErrors.Count -gt 0) {
        Write-Log "" "White"
        Write-Log "🚨 ERROR SUMMARY:" "Red"
        $errorGroups = $allErrors | Group-Object -Property Error | Sort-Object Count -Descending
        foreach ($group in $errorGroups) {
            Write-Log "   $($group.Count)x: $($group.Name)" "Red"
        }
    }
}

# Main execution
Write-Log "🚀 Starting SocioRAG Load Testing" "Green"
Write-Log "=================================" "Green"
Write-Log "👥 Concurrent Users: $ConcurrentUsers" "Cyan"
Write-Log "⏱️  Test Duration: $TestDurationMinutes minutes" "Cyan"
Write-Log "⏳ Request Delay: $RequestDelaySeconds seconds" "Cyan"
Write-Log "📁 Results will be saved to: $RESULTS_FILE" "Cyan"

# Test backend connectivity
Write-Log "🔍 Testing backend connectivity..." "Cyan"
try {
    $healthCheck = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -TimeoutSec 10
    Write-Log "✅ Backend is accessible, status: $($healthCheck.status)" "Green"
}
catch {
    Write-Log "❌ Cannot connect to backend: $($_.Exception.Message)" "Red"
    Write-Log "💡 Please ensure SocioRAG is running at $BACKEND_URL" "Yellow"
    exit 1
}

# Load test queries
$queries = Get-TestQueries

# Create test queries file if it doesn't exist
if (-not (Test-Path $TestQueries)) {
    Write-Log "📝 Creating test queries file at $TestQueries" "Yellow"
    $DefaultQueries | Out-File -FilePath $TestQueries -Encoding UTF8
}

# Start user simulations
Write-Log "🏁 Starting load test with $ConcurrentUsers concurrent users..." "Green"

$jobs = @()
for ($i = 1; $i -le $ConcurrentUsers; $i++) {
    $job = Start-Job -ScriptBlock {
        param($UserId, $Queries, $TestDurationMinutes, $DelaySeconds, $BackendUrl, $LogFile)
        
        # Import the Test-APIEndpoint function and other dependencies
        function Test-APIEndpoint {
            param($Method, $Uri, $Body = $null, $TimeoutSec = 30)
            
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            
            try {
                $params = @{
                    Uri = "$BackendUrl$Uri"
                    Method = $Method
                    TimeoutSec = $TimeoutSec
                    ErrorAction = "Stop"
                }
                
                if ($Body) {
                    $params.Body = $Body | ConvertTo-Json
                    $params.ContentType = "application/json"
                }
                
                $response = Invoke-RestMethod @params
                $stopwatch.Stop()
                
                return @{
                    Success = $true
                    ResponseTime = $stopwatch.ElapsedMilliseconds
                    StatusCode = 200
                    Response = $response
                }
            }
            catch {
                $stopwatch.Stop()
                return @{
                    Success = $false
                    ResponseTime = $stopwatch.ElapsedMilliseconds
                    Error = $_.Exception.Message
                    StatusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode } else { "Unknown" }
                }
            }
        }
        
        # User simulation logic
        $endTime = (Get-Date).AddMinutes($TestDurationMinutes)
        $userResults = @{
            UserId = $UserId
            TotalRequests = 0
            SuccessfulRequests = 0
            FailedRequests = 0
            TotalResponseTime = 0
            MinResponseTime = [int]::MaxValue
            MaxResponseTime = 0
            Errors = @()
            StartTime = Get-Date
        }
        
        while ((Get-Date) -lt $endTime) {
            # Random query selection
            $query = $Queries | Get-Random
            
            # Test health check
            $healthResult = Test-APIEndpoint -Method "GET" -Uri "/api/admin/health" -TimeoutSec 10
            $userResults.TotalRequests++
            
            if ($healthResult.Success) {
                $userResults.SuccessfulRequests++
                $userResults.TotalResponseTime += $healthResult.ResponseTime
                $userResults.MinResponseTime = [math]::Min($userResults.MinResponseTime, $healthResult.ResponseTime)
                $userResults.MaxResponseTime = [math]::Max($userResults.MaxResponseTime, $healthResult.ResponseTime)
            }
            else {
                $userResults.FailedRequests++
                $userResults.Errors += @{
                    Timestamp = Get-Date
                    Endpoint = "/api/admin/health"
                    Error = $healthResult.Error
                }
            }
            
            # Test metrics endpoint
            $metricsResult = Test-APIEndpoint -Method "GET" -Uri "/api/admin/metrics" -TimeoutSec 10
            $userResults.TotalRequests++
            
            if ($metricsResult.Success) {
                $userResults.SuccessfulRequests++
                $userResults.TotalResponseTime += $metricsResult.ResponseTime
                $userResults.MinResponseTime = [math]::Min($userResults.MinResponseTime, $metricsResult.ResponseTime)
                $userResults.MaxResponseTime = [math]::Max($userResults.MaxResponseTime, $metricsResult.ResponseTime)
            }
            else {
                $userResults.FailedRequests++
                $userResults.Errors += @{
                    Timestamp = Get-Date
                    Endpoint = "/api/admin/metrics"
                    Error = $metricsResult.Error
                }
            }
            
            # Wait between requests
            Start-Sleep -Seconds $DelaySeconds
        }
        
        $userResults.EndTime = Get-Date
        $userResults.TestDuration = ($userResults.EndTime - $userResults.StartTime).TotalMinutes
        $userResults.AverageResponseTime = if ($userResults.SuccessfulRequests -gt 0) { 
            [math]::Round($userResults.TotalResponseTime / $userResults.SuccessfulRequests, 2) 
        } else { 0 }
        $userResults.SuccessRate = if ($userResults.TotalRequests -gt 0) { 
            [math]::Round(($userResults.SuccessfulRequests / $userResults.TotalRequests) * 100, 2) 
        } else { 0 }
        
        return $userResults
        
    } -ArgumentList $i, $queries, $TestDurationMinutes, $RequestDelaySeconds, $BACKEND_URL, $LOG_FILE
    
    $jobs += $job
    Write-Log "👤 Started user simulation $i (Job ID: $($job.Id))" "Cyan"
}

# Monitor progress
Write-Log "⏳ Load test in progress..." "Yellow"
$startTime = Get-Date
while ($jobs | Where-Object { $_.State -eq "Running" }) {
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    $remaining = [math]::Max($TestDurationMinutes - $elapsed, 0)
    Write-Log "⏱️  Elapsed: ${elapsed}m, Remaining: ${remaining}m" "Gray"
    Start-Sleep -Seconds 30
}

# Collect results
Write-Log "📊 Collecting results..." "Cyan"
$results = @()
foreach ($job in $jobs) {
    try {
        $result = Receive-Job -Job $job -Wait
        $results += $result
        Remove-Job -Job $job
    }
    catch {
        Write-Log "❌ Error collecting results from job $($job.Id): $($_.Exception.Message)" "Red"
    }
}

# Save results to file
try {
    $testSummary = @{
        Timestamp = Get-Date
        Configuration = @{
            ConcurrentUsers = $ConcurrentUsers
            TestDurationMinutes = $TestDurationMinutes
            RequestDelaySeconds = $RequestDelaySeconds
            BackendUrl = $BACKEND_URL
        }
        Results = $results
    }
    
    $testSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath $RESULTS_FILE -Encoding UTF8
    Write-Log "💾 Results saved to: $RESULTS_FILE" "Green"
}
catch {
    Write-Log "❌ Error saving results: $($_.Exception.Message)" "Red"
}

# Show summary
Show-LoadTestSummary -Results $results

Write-Log "" "White"
Write-Log "✅ Load test completed!" "Green"
Write-Log "📁 Detailed results: $RESULTS_FILE" "Cyan"
Write-Log "📁 Test log: $LOG_FILE" "Cyan"
