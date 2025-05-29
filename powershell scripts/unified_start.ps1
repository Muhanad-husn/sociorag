# SocioRAG Unified Startup Script
# Manages both backend and frontend in a single coordinated process
# Enables proper monitoring and graceful shutdown

param(
    [switch]$MonitoringMode,
    [switch]$DevMode,
    [switch]$SkipBrowser,
    [int]$HealthCheckInterval = 30
)

# Configuration
$BACKEND_PORT = 8000
$FRONTEND_PORT = 5173
$BACKEND_URL = "http://127.0.0.1:$BACKEND_PORT"
$FRONTEND_URL = "http://localhost:$FRONTEND_PORT"
$LOG_FILE = "logs\unified_start_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Ensure logs directory exists
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Global variables for process management
$script:BackendJob = $null
$script:FrontendJob = $null
$script:MonitoringJob = $null
$script:IsShuttingDown = $false

function Write-Log {
    param($Message, $Color = "White", $Component = "MAIN")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp][$Component] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $LOG_FILE -Value $logMessage
}

function Test-Port {
    param($Port)
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ConnectAsync("127.0.0.1", $Port).Wait(1000)
        $result = $tcpClient.Connected
        $tcpClient.Close()
        return $result
    }
    catch {
        return $false
    }
}

function Test-BackendHealth {
    try {
        $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -TimeoutSec 5 -ErrorAction Stop
        return @{
            IsHealthy = $true
            Status = $response.status
            Response = $response
        }
    }
    catch {
        return @{
            IsHealthy = $false
            Error = $_.Exception.Message
        }
    }
}

function Test-FrontendHealth {
    try {
        $response = Invoke-WebRequest -Uri $FRONTEND_URL -TimeoutSec 5 -ErrorAction Stop
        return @{
            IsHealthy = ($response.StatusCode -eq 200)
            StatusCode = $response.StatusCode
        }
    }
    catch {
        return @{
            IsHealthy = $false
            Error = $_.Exception.Message
        }
    }
}

function Start-BackendService {
    Write-Log "🔧 Starting backend service..." "Cyan" "BACKEND"
    
    # Kill any existing backend processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*backend.app.main*" } | 
        ForEach-Object { 
            Write-Log "🛑 Stopping existing backend process (PID: $($_.Id))" "Yellow" "BACKEND"
            Stop-Process -Id $_.Id -Force 
        }
    
    $script:BackendJob = Start-Job -ScriptBlock {
        param($WorkingDir, $LogFile)
        
        function Write-JobLog {
            param($Message, $Component = "BACKEND")
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logMessage = "[$timestamp][$Component] $Message"
            Add-Content -Path $LogFile -Value $logMessage
        }
        
        Set-Location $WorkingDir
        Write-JobLog "Backend starting from: $WorkingDir"
        
        try {
            # Start backend with proper output handling
            $process = Start-Process -FilePath "python" -ArgumentList "-m", "backend.app.main" -NoNewWindow -PassThru -RedirectStandardOutput "logs\backend_output.log" -RedirectStandardError "logs\backend_error.log"
            
            Write-JobLog "Backend process started with PID: $($process.Id)"
            
            # Monitor the process
            while (-not $process.HasExited) {
                Start-Sleep -Seconds 5
            }
            
            Write-JobLog "Backend process exited with code: $($process.ExitCode)"
            return $process.ExitCode
        }
        catch {
            Write-JobLog "Backend startup error: $($_.Exception.Message)"
            return -1
        }
    } -ArgumentList $PWD.Path, $LOG_FILE
    
    # Wait for backend to be ready
    Write-Log "⏳ Waiting for backend to initialize..." "Yellow" "BACKEND"
    $attempts = 0
    $maxAttempts = 30
    
    do {
        Start-Sleep -Seconds 2
        $attempts++
        
        if (Test-Port -Port $BACKEND_PORT) {
            $health = Test-BackendHealth
            if ($health.IsHealthy) {
                Write-Log "✅ Backend is ready and healthy!" "Green" "BACKEND"
                return $true
            }
        }
        
        if ($attempts % 5 -eq 0) {
            Write-Log "   Still waiting... (attempt $attempts/$maxAttempts)" "Yellow" "BACKEND"
        }
        
        # Check if backend job failed
        if ($script:BackendJob.State -eq "Failed" -or $script:BackendJob.State -eq "Completed") {
            Write-Log "❌ Backend job failed or completed unexpectedly" "Red" "BACKEND"
            return $false
        }
        
    } while ($attempts -lt $maxAttempts)
    
    Write-Log "❌ Backend failed to start within $maxAttempts attempts" "Red" "BACKEND"
    return $false
}

function Start-FrontendService {
    Write-Log "🎨 Starting frontend service..." "Cyan" "FRONTEND"
    
    # Check if frontend directory exists
    if (-not (Test-Path "ui")) {
        Write-Log "❌ Frontend directory 'ui' not found" "Red" "FRONTEND"
        return $false
    }
    
    # Kill any existing frontend processes
    Get-Process -Name "node" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*dev*" } | 
        ForEach-Object { 
            Write-Log "🛑 Stopping existing frontend process (PID: $($_.Id))" "Yellow" "FRONTEND"
            Stop-Process -Id $_.Id -Force 
        }
    
    $script:FrontendJob = Start-Job -ScriptBlock {
        param($WorkingDir, $LogFile)
        
        function Write-JobLog {
            param($Message, $Component = "FRONTEND")
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logMessage = "[$timestamp][$Component] $Message"
            Add-Content -Path $LogFile -Value $logMessage
        }
        
        Set-Location "$WorkingDir\ui"
        Write-JobLog "Frontend starting from: $PWD"
        
        try {
            # Check if pnpm is available, fallback to npm
            $packageManager = if (Get-Command pnpm -ErrorAction SilentlyContinue) { "pnpm" } else { "npm" }
            Write-JobLog "Using package manager: $packageManager"
            
            # Start frontend with proper output handling
            $process = Start-Process -FilePath $packageManager -ArgumentList "run", "dev" -NoNewWindow -PassThru -RedirectStandardOutput "..\logs\frontend_output.log" -RedirectStandardError "..\logs\frontend_error.log"
            
            Write-JobLog "Frontend process started with PID: $($process.Id)"
            
            # Monitor the process
            while (-not $process.HasExited) {
                Start-Sleep -Seconds 5
            }
            
            Write-JobLog "Frontend process exited with code: $($process.ExitCode)"
            return $process.ExitCode
        }
        catch {
            Write-JobLog "Frontend startup error: $($_.Exception.Message)"
            return -1
        }
    } -ArgumentList $PWD.Path, $LOG_FILE
    
    # Wait for frontend to be ready
    Write-Log "⏳ Waiting for frontend to initialize..." "Yellow" "FRONTEND"
    $attempts = 0
    $maxAttempts = 20
    
    do {
        Start-Sleep -Seconds 3
        $attempts++
        
        if (Test-Port -Port $FRONTEND_PORT) {
            $health = Test-FrontendHealth
            if ($health.IsHealthy) {
                Write-Log "✅ Frontend is ready and serving!" "Green" "FRONTEND"
                return $true
            }
        }
        
        if ($attempts % 3 -eq 0) {
            Write-Log "   Still waiting... (attempt $attempts/$maxAttempts)" "Yellow" "FRONTEND"
        }
        
        # Check if frontend job failed
        if ($script:FrontendJob.State -eq "Failed" -or $script:FrontendJob.State -eq "Completed") {
            Write-Log "❌ Frontend job failed or completed unexpectedly" "Red" "FRONTEND"
            return $false
        }
        
    } while ($attempts -lt $maxAttempts)
    
    Write-Log "❌ Frontend failed to start within $maxAttempts attempts" "Red" "FRONTEND"
    return $false
}

function Start-MonitoringService {
    if (-not $MonitoringMode) { return }
    
    Write-Log "📊 Starting monitoring service..." "Cyan" "MONITOR"
    
    $script:MonitoringJob = Start-Job -ScriptBlock {
        param($BackendUrl, $FrontendUrl, $HealthCheckInterval, $LogFile)
        
        function Write-JobLog {
            param($Message, $Component = "MONITOR")
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logMessage = "[$timestamp][$Component] $Message"
            Add-Content -Path $LogFile -Value $logMessage
        }
        
        function Test-ServiceHealth {
            param($Url, $ServiceName)
            try {
                $response = Invoke-RestMethod -Uri $Url -TimeoutSec 5 -ErrorAction Stop
                return @{
                    Service = $ServiceName
                    IsHealthy = $true
                    ResponseTime = (Measure-Command { Invoke-RestMethod -Uri $Url -TimeoutSec 5 }).TotalMilliseconds
                    Status = if ($response.status) { $response.status } else { "OK" }
                }
            }
            catch {
                return @{
                    Service = $ServiceName
                    IsHealthy = $false
                    Error = $_.Exception.Message
                }
            }
        }
        
        Write-JobLog "Monitoring started with $HealthCheckInterval second intervals"
        
        while ($true) {
            # Check backend health
            $backendHealth = Test-ServiceHealth -Url "$BackendUrl/api/admin/health" -ServiceName "Backend"
            
            # Check frontend health  
            $frontendHealth = Test-ServiceHealth -Url $FrontendUrl -ServiceName "Frontend"
            
            # Log health status
            $backendStatus = if ($backendHealth.IsHealthy) { "✅ HEALTHY" } else { "❌ UNHEALTHY" }
            $frontendStatus = if ($frontendHealth.IsHealthy) { "✅ HEALTHY" } else { "❌ UNHEALTHY" }
            
            Write-JobLog "Backend: $backendStatus, Frontend: $frontendStatus"
            
            if ($backendHealth.IsHealthy) {
                Write-JobLog "Backend response time: $([math]::Round($backendHealth.ResponseTime, 2))ms"
            } else {
                Write-JobLog "Backend error: $($backendHealth.Error)"
            }
            
            if (-not $frontendHealth.IsHealthy) {
                Write-JobLog "Frontend error: $($frontendHealth.Error)"
            }
            
            Start-Sleep -Seconds $HealthCheckInterval
        }
    } -ArgumentList $BACKEND_URL, $FRONTEND_URL, $HealthCheckInterval, $LOG_FILE
}

function Stop-AllServices {
    $script:IsShuttingDown = $true
    Write-Log "🛑 Shutting down all services..." "Yellow" "SHUTDOWN"
    
    # Stop monitoring
    if ($script:MonitoringJob) {
        Stop-Job -Job $script:MonitoringJob -PassThru | Remove-Job
        Write-Log "✅ Monitoring service stopped" "Green" "SHUTDOWN"
    }
    
    # Stop frontend
    if ($script:FrontendJob) {
        Stop-Job -Job $script:FrontendJob -PassThru | Remove-Job
        Write-Log "✅ Frontend service stopped" "Green" "SHUTDOWN"
    }
    
    # Stop backend
    if ($script:BackendJob) {
        Stop-Job -Job $script:BackendJob -PassThru | Remove-Job
        Write-Log "✅ Backend service stopped" "Green" "SHUTDOWN"
    }
    
    # Kill any remaining processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*backend.app.main*" } | 
        ForEach-Object { Stop-Process -Id $_.Id -Force }
    
    Get-Process -Name "node" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*dev*" } | 
        ForEach-Object { Stop-Process -Id $_.Id -Force }
    
    Write-Log "🏁 All services stopped" "Green" "SHUTDOWN"
}

function Show-ServiceStatus {
    Write-Log "📋 SERVICE STATUS" "Cyan" "STATUS"
    Write-Log "=================" "Cyan" "STATUS"
    
    # Backend status
    $backendHealth = Test-BackendHealth
    if ($backendHealth.IsHealthy) {
        Write-Log "🔧 Backend: ✅ HEALTHY ($($backendHealth.Status))" "Green" "STATUS"
    } else {
        Write-Log "🔧 Backend: ❌ UNHEALTHY ($($backendHealth.Error))" "Red" "STATUS"
    }
    
    # Frontend status
    $frontendHealth = Test-FrontendHealth
    if ($frontendHealth.IsHealthy) {
        Write-Log "🎨 Frontend: ✅ HEALTHY (HTTP $($frontendHealth.StatusCode))" "Green" "STATUS"
    } else {
        Write-Log "🎨 Frontend: ❌ UNHEALTHY ($($frontendHealth.Error))" "Red" "STATUS"
    }
    
    # Job status
    if ($script:BackendJob) {
        Write-Log "🔧 Backend Job: $($script:BackendJob.State)" "White" "STATUS"
    }
    if ($script:FrontendJob) {
        Write-Log "🎨 Frontend Job: $($script:FrontendJob.State)" "White" "STATUS"
    }
    if ($script:MonitoringJob) {
        Write-Log "📊 Monitoring Job: $($script:MonitoringJob.State)" "White" "STATUS"
    }
}

# Handle Ctrl+C gracefully
Register-EngineEvent -SourceIdentifier "PowerShell.Exiting" -Action {
    if (-not $script:IsShuttingDown) {
        Stop-AllServices
    }
}

# Main execution
try {
    Write-Log "🚀 SocioRAG Unified Startup" "Green"
    Write-Log "============================" "Green"
    Write-Log "📁 Working Directory: $($PWD.Path)" "Cyan"
    Write-Log "📝 Log File: $LOG_FILE" "Cyan"
    
    if ($MonitoringMode) {
        Write-Log "📊 Monitoring mode enabled" "Cyan"
    }
    if ($DevMode) {
        Write-Log "🔧 Development mode enabled" "Cyan"
    }
    
    # Validate directory structure
    if (-not (Test-Path "backend\app\main.py")) {
        Write-Log "❌ Error: Run this from the SocioRAG root directory" "Red"
        exit 1
    }
    
    # Start backend
    if (-not (Start-BackendService)) {
        Write-Log "❌ Failed to start backend service" "Red"
        exit 1
    }
    
    # Start frontend
    if (-not (Start-FrontendService)) {
        Write-Log "❌ Failed to start frontend service" "Red"
        Stop-AllServices
        exit 1
    }
    
    # Start monitoring if requested
    Start-MonitoringService
    
    # Show status
    Start-Sleep -Seconds 2
    Show-ServiceStatus
    
    # Display URLs
    Write-Log "" "White"
    Write-Log "🎉 SocioRAG is Ready!" "Green"
    Write-Log "=====================" "Green"
    Write-Log "🎨 Frontend:  $FRONTEND_URL" "White"
    Write-Log "🔧 Backend:   $BACKEND_URL" "White"
    Write-Log "📚 API Docs:  $BACKEND_URL/docs" "White"
    Write-Log "📊 Admin:     $BACKEND_URL/api/admin/status" "White"
    Write-Log "📝 Logs:      $LOG_FILE" "White"
    
    # Open browser unless skipped
    if (-not $SkipBrowser) {
        Write-Log "🌐 Opening frontend in your browser..." "Cyan"
        Start-Process $FRONTEND_URL
    }
    
    Write-Log "" "White"
    Write-Log "💡 USAGE:" "Cyan"
    Write-Log "   • Press 'S' to show service status" "White"
    Write-Log "   • Press 'L' to view recent logs" "White"
    Write-Log "   • Press 'Q' or Ctrl+C to quit" "White"
    Write-Log "" "White"
    
    # Interactive mode
    while (-not $script:IsShuttingDown) {
        $key = $null
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true).KeyChar.ToString().ToUpper()
        }
        
        switch ($key) {
            'S' { 
                Show-ServiceStatus 
            }
            'L' { 
                Write-Log "📋 Recent log entries:" "Cyan"
                Get-Content $LOG_FILE -Tail 10 | ForEach-Object { Write-Host $_ }
            }
            'Q' { 
                break 
            }
        }
        
        # Check job health
        if ($script:BackendJob -and $script:BackendJob.State -eq "Failed") {
            Write-Log "❌ Backend job failed!" "Red"
            break
        }
        if ($script:FrontendJob -and $script:FrontendJob.State -eq "Failed") {
            Write-Log "❌ Frontend job failed!" "Red"
            break
        }
        
        Start-Sleep -Seconds 1
    }
    
}
catch {
    Write-Log "❌ Unexpected error: $($_.Exception.Message)" "Red"
}
finally {
    Stop-AllServices
    Write-Log "👋 SocioRAG shutdown complete" "Green"
}
