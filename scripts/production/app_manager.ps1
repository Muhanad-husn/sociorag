# SocioRAG Application Manager
# Coordinates backend and frontend startup with proper monitoring integration
# Designed to work seamlessly with performance testing and monitoring scripts

param(
    [ValidateSet("start", "stop", "restart", "status", "clean")]
    [string]$Action = "start",
    
    [switch]$WaitForReady,
    [switch]$SkipBrowser,
    [switch]$EnableMonitoring,
    [int]$TimeoutSeconds = 60
)

# Ensure we're working from the project root
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $ProjectRoot

# Configuration
$CONFIG = @{
    BackendPort = 8000
    FrontendPort = 5173
    BackendUrl = "http://127.0.0.1:8000"
    FrontendUrl = "http://localhost:5173"
    PidFile = "logs\sociorag.pid"
    LogFile = "logs\app_manager.log"
    AppLogFile = "logs\sociorag_application.log"
}

# Ensure logs directory exists
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

function Write-AppLog {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp][$Level] $Message"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    Write-Host $logMessage -ForegroundColor $color
    Add-Content -Path $CONFIG.LogFile -Value $logMessage
}

function Test-ServiceHealth {
    param($Url, $TimeoutSec = 5, [switch]$IsFrontend)
    try {
        if ($IsFrontend) {
            # For frontend, we just check if the port is listening
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $portOpen = $tcpClient.ConnectAsync("localhost", 5173).Wait($TimeoutSec * 1000)
            $tcpClient.Close()
            
            if ($portOpen) {
                return @{
                    IsHealthy = $true
                    ResponseTime = 0
                }
            } else {
                return @{
                    IsHealthy = $false
                    Error = "Frontend port 5173 is not accessible"
                }
            }
        } else {
            # For backend or other services, we use Invoke-RestMethod
            $response = Invoke-RestMethod -Uri $Url -TimeoutSec $TimeoutSec -ErrorAction Stop
            return @{
                IsHealthy = $true
                Response = $response
                ResponseTime = (Measure-Command { 
                    Invoke-RestMethod -Uri $Url -TimeoutSec $TimeoutSec 
                }).TotalMilliseconds
            }
        }
    }
    catch {
        return @{
            IsHealthy = $false
            Error = $_.Exception.Message
        }
    }
}

function Start-BackendProcess {
    Write-AppLog "Starting backend process..." "INFO"
    
    # Check if already running
    $existingBackend = Get-Process -Name "python" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*backend.app.main*" }
    
    if ($existingBackend) {
        Write-AppLog "Backend already running (PID: $($existingBackend.Id))" "WARNING"
        return $existingBackend
    }      try {
        # Create a unique temp error log that will be merged into the main log
        $tempErrorLog = "logs\temp_stderr_$([Guid]::NewGuid().ToString()).log"
        
        # Start process with separate output and error redirections
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "backend.app.main" `
            -WorkingDirectory $PWD -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput "logs\sociorag_application.log" `
            -RedirectStandardError $tempErrorLog
        
        # Start background job to append error log to main log and then delete it
        Start-Job -ScriptBlock {
            param($tempLog, $mainLog)
            # Wait a moment to ensure the process has started writing to the log
            Start-Sleep -Seconds 2
            # Keep monitoring and merging logs until the application stops
            while (Test-Path $tempLog) {
                if ((Get-Item $tempLog).Length -gt 0) {
                    Get-Content $tempLog | Add-Content $mainLog
                    Clear-Content $tempLog
                }
                Start-Sleep -Seconds 3
            }
        } -ArgumentList $tempErrorLog, "logs\sociorag_application.log" | Out-Null
        
        Write-AppLog "Backend started with PID: $($process.Id)" "SUCCESS"
        return $process
    }
    catch {
        Write-AppLog "Failed to start backend: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

function Install-FrontendDependencies {
    Write-AppLog "Checking frontend dependencies..." "INFO"
    
    if (-not (Test-Path "ui\node_modules")) {
        Write-AppLog "Frontend dependencies not found. Installing..." "INFO"
        
        try {
            # Determine package manager
            $packageManager = "npm"
            if (Test-Path "ui\pnpm-lock.yaml") {
                $packageManager = "pnpm"
            } elseif (Test-Path "ui\yarn.lock") {
                $packageManager = "yarn"
            }
            
            Write-AppLog "Installing dependencies using $packageManager..." "INFO"
            
            # Get full path to package manager
            $packageManagerPath = $null
            if ($packageManager -eq "npm") {
                $packageManagerPath = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
                if (-not $packageManagerPath) {
                    $packageManagerPath = "npm"
                }
            } else {
                $packageManagerPath = $packageManager
            }
            
            # Install dependencies in UI directory
            $installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$packageManagerPath`"", "install" `
                -WorkingDirectory "ui" -Wait -PassThru -NoNewWindow
            
            if ($installProcess.ExitCode -eq 0) {
                Write-AppLog "Frontend dependencies installed successfully!" "SUCCESS"
                return $true
            } else {
                Write-AppLog "Failed to install frontend dependencies (Exit code: $($installProcess.ExitCode))" "ERROR"
                return $false
            }
        }
        catch {
            Write-AppLog "Error installing frontend dependencies: $($_.Exception.Message)" "ERROR"
            return $false
        }
    } else {
        Write-AppLog "Frontend dependencies already installed" "INFO"
        return $true
    }
}

function Start-FrontendProcess {
    Write-AppLog "Starting frontend process..." "INFO"
    
    # Check if already running
    $existingFrontend = Get-Process -Name "node", "pnpm", "npm" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*dev*" }
    
    if ($existingFrontend) {
        Write-AppLog "Frontend already running (PID: $($existingFrontend.Id))" "WARNING"
        return $existingFrontend
    }
    
    if (-not (Test-Path "ui")) {
        Write-AppLog "Frontend directory 'ui' not found" "ERROR"
        return $null
    }
    
    # Install dependencies if needed
    if (-not (Install-FrontendDependencies)) {
        Write-AppLog "Cannot start frontend without dependencies" "ERROR"
        return $null
    }try {
        # Get the full path to the package manager executable
        $packageManagerPath = $null
        $packageManagerType = $null
        
        if (Get-Command pnpm -ErrorAction SilentlyContinue) {
            $packageManagerPath = (Get-Command pnpm.cmd -ErrorAction SilentlyContinue).Source
            if (-not $packageManagerPath) {
                $packageManagerPath = (Get-Command pnpm.ps1 -ErrorAction SilentlyContinue).Source
            }
            if (-not $packageManagerPath) {
                $packageManagerPath = "pnpm.cmd" # Fallback to searching in PATH
            }
            $packageManagerType = "pnpm"
        } else {
            $packageManagerPath = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
            if (-not $packageManagerPath) {
                $packageManagerPath = (Get-Command npm.ps1 -ErrorAction SilentlyContinue).Source
            }
            if (-not $packageManagerPath) {
                $packageManagerPath = "npm.cmd" # Fallback to searching in PATH
            }
            $packageManagerType = "npm"
        }        Write-AppLog "Using package manager: $packageManagerType ($packageManagerPath)" "INFO"
        
        # Use the same approach as backend for merging logs
        $tempErrorLog = "logs\temp_frontend_stderr_$([Guid]::NewGuid().ToString()).log"
        $quotedPath = "`"$packageManagerPath`""
        $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "$quotedPath", "run", "dev" `
            -WorkingDirectory "ui" -PassThru -NoNewWindow `
            -RedirectStandardOutput "logs\sociorag_application.log" `
            -RedirectStandardError $tempErrorLog
        
        # Start background job to append error log to main log and then delete it
        Start-Job -ScriptBlock {
            param($tempLog, $mainLog)
            # Wait a moment to ensure the process has started writing to the log
            Start-Sleep -Seconds 2
            # Keep monitoring and merging logs until the application stops
            while (Test-Path $tempLog) {
                if ((Get-Item $tempLog).Length -gt 0) {
                    Get-Content $tempLog | Add-Content $mainLog
                    Clear-Content $tempLog
                }
                Start-Sleep -Seconds 3
            }
        } -ArgumentList $tempErrorLog, "logs\sociorag_application.log" | Out-Null
        
        Write-AppLog "Frontend started with PID: $($process.Id) using $packageManagerType" "SUCCESS"
        return $process
    }
    catch {
        Write-AppLog "Failed to start frontend: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

function Wait-ForServices {
    param($TimeoutSeconds = 60)
    
    Write-AppLog "Waiting for services to be ready (timeout: ${TimeoutSeconds}s)..." "INFO"
    
    $startTime = Get-Date
    $backendReady = $false
    $frontendReady = $false
      while (((Get-Date) - $startTime).TotalSeconds -lt $TimeoutSeconds) {
        # Check backend
        if (-not $backendReady) {
            $backendHealth = Test-ServiceHealth -Url "$($CONFIG.BackendUrl)/api/admin/health"
            if ($backendHealth.IsHealthy) {
                Write-AppLog "Backend is ready and healthy!" "SUCCESS"
                $backendReady = $true
            }
        }
        
        # Check frontend  
        if (-not $frontendReady) {
            $frontendHealth = Test-ServiceHealth -Url $CONFIG.FrontendUrl -IsFrontend
            if ($frontendHealth.IsHealthy) {
                Write-AppLog "Frontend is ready and serving!" "SUCCESS"
                $frontendReady = $true
            }
        }
        
        if ($backendReady -and $frontendReady) {
            return $true
        }
        
        Start-Sleep -Seconds 2
    }
    
    Write-AppLog "Services failed to become ready within timeout" "ERROR"
    return $false
}

function Cleanup-LogFiles {
    param(
        [int]$RetainCount = 3,
        [switch]$Force
    )
    
    Write-AppLog "Cleaning up log files..." "INFO"
      # Define log file patterns to consolidate
    $logPatterns = @(
        "frontend_*.log",
        "sociorag_debug*.log",
        "temp_stderr_*.log",
        "temp_frontend_stderr_*.log"
    )
    
    $consolidated = 0
    $removed = 0
    
    # Process each log pattern
    foreach ($pattern in $logPatterns) {
        $logFiles = Get-ChildItem -Path "logs" -Filter $pattern -ErrorAction SilentlyContinue
        
        foreach ($logFile in $logFiles) {
            try {
                # Append content to application log if it's not empty
                if ((Get-Item $logFile.FullName).Length -gt 0) {
                    Add-Content -Path $CONFIG.AppLogFile -Value "`n--- Consolidated from $($logFile.Name) on $(Get-Date) ---`n"
                    Get-Content -Path $logFile.FullName | Add-Content -Path $CONFIG.AppLogFile
                    $consolidated++
                }
                
                # Remove the file
                Remove-Item -Path $logFile.FullName -Force
                $removed++
                Write-AppLog "Consolidated and removed $($logFile.Name)" "SUCCESS"
            }
            catch {
                Write-AppLog "Failed to process $($logFile.Name): $($_.Exception.Message)" "ERROR"
            }
        }
    }
    
    # Keep only N most recent rotated log files
    $rotatedLogs = Get-ChildItem -Path "logs" -Filter "*.log.*" -ErrorAction SilentlyContinue
    
    # Group by base log name
    $groupedLogs = $rotatedLogs | Group-Object { $_.Name -replace '\.\d+$', '' }
    
    foreach ($group in $groupedLogs) {
        # Sort by newest (highest number = newest in rotation scheme)
        $sortedLogs = $group.Group | Sort-Object { 
            if ($_.Name -match '\.(\d+)$') { [int]$matches[1] } else { 0 } 
        } -Descending
        
        # Skip the most recent N files
        $logsToRemove = $sortedLogs | Select-Object -Skip $RetainCount
        
        foreach ($log in $logsToRemove) {
            try {
                Remove-Item -Path $log.FullName -Force
                $removed++
                Write-AppLog "Removed old rotated log file: $($log.Name)" "INFO"
            }
            catch {
                Write-AppLog "Failed to remove $($log.Name): $($_.Exception.Message)" "ERROR"
            }
        }
    }
    
    Write-AppLog "Log cleanup completed: $consolidated files consolidated, $removed files removed" "SUCCESS"
}

function Stop-SocioRAGServices {
    Write-AppLog "Stopping SocioRAG services..." "INFO"
    
    $stopped = 0
    
    # Stop backend processes
    $backendProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*backend.app.main*" }
    
    foreach ($process in $backendProcesses) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-AppLog "Stopped backend process (PID: $($process.Id))" "SUCCESS"
            $stopped++
        }
        catch {
            Write-AppLog "Failed to stop backend process (PID: $($process.Id)): $($_.Exception.Message)" "ERROR"
        }
    }
      # Stop frontend processes
    $frontendProcesses = Get-Process -Name "node", "pnpm", "npm" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*dev*" }
    
    foreach ($process in $frontendProcesses) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-AppLog "Stopped frontend process (PID: $($process.Id))" "SUCCESS"
            $stopped++
        }
        catch {
            Write-AppLog "Failed to stop frontend process (PID: $($process.Id)): $($_.Exception.Message)" "ERROR"
        }
    }
      if ($stopped -eq 0) {
        Write-AppLog "No SocioRAG processes found to stop" "WARNING"
    } else {
        Write-AppLog "Stopped $stopped processes" "SUCCESS"
    }
    
    # Clean up temp log files
    $tempLogFiles = Get-ChildItem -Path "logs" -Filter "temp_*stderr_*.log" -ErrorAction SilentlyContinue
    foreach ($logFile in $tempLogFiles) {
        try {
            # Append content to application log if it's not empty
            if ((Get-Item $logFile.FullName).Length -gt 0) {
                Add-Content -Path $CONFIG.AppLogFile -Value "`n--- Final content from $($logFile.Name) on $(Get-Date) ---`n"
                Get-Content -Path $logFile.FullName | Add-Content -Path $CONFIG.AppLogFile
            }
            
            # Remove the file
            Remove-Item -Path $logFile.FullName -Force
            Write-AppLog "Cleaned up temporary log file: $($logFile.Name)" "INFO"
        }
        catch {
            Write-AppLog "Failed to clean up $($logFile.Name): $($_.Exception.Message)" "ERROR"
        }
    }
    
    # Stop background log monitoring jobs
    $logJobs = Get-Job | Where-Object { $_.Command -like "*tempLog*mainLog*" }
    if ($logJobs) {
        $logJobs | Stop-Job -PassThru | Remove-Job -Force
        Write-AppLog "Stopped $($logJobs.Count) background log monitoring jobs" "INFO"
    }
    
    # Clean up PID file
    if (Test-Path $CONFIG.PidFile) {
        Remove-Item $CONFIG.PidFile -Force
    }
}

function Get-ServiceStatus {
    Write-AppLog "Checking service status..." "INFO"
    
    # Check processes
    $backendProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*backend.app.main*" }
    $frontendProcesses = Get-Process -Name "node", "pnpm", "npm" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*dev*" }
    
    # Check health
    $backendHealth = Test-ServiceHealth -Url "$($CONFIG.BackendUrl)/api/admin/health"
    $frontendHealth = Test-ServiceHealth -Url $CONFIG.FrontendUrl -IsFrontend
    
    $status = @{
        Backend = @{
            ProcessCount = $backendProcesses.Count
            PIDs = $backendProcesses | ForEach-Object { $_.Id }
            IsHealthy = $backendHealth.IsHealthy
            ResponseTime = $backendHealth.ResponseTime
            Error = $backendHealth.Error
        }
        Frontend = @{
            ProcessCount = $frontendProcesses.Count
            PIDs = $frontendProcesses | ForEach-Object { $_.Id }
            IsHealthy = $frontendHealth.IsHealthy
            Error = $frontendHealth.Error
        }
        URLs = $CONFIG
    }
    
    # Display status
    Write-Host ""
    Write-Host "📊 SocioRAG Service Status" -ForegroundColor Green
    Write-Host "=========================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔧 Backend:" -ForegroundColor Cyan
    Write-Host "   Processes: $($status.Backend.ProcessCount) $(if($status.Backend.PIDs) { "($($status.Backend.PIDs -join ', '))" })" -ForegroundColor White
    Write-Host "   Health: $(if($status.Backend.IsHealthy) { '✅ HEALTHY' } else { '❌ UNHEALTHY' })" -ForegroundColor $(if($status.Backend.IsHealthy) { 'Green' } else { 'Red' })
    if ($status.Backend.ResponseTime) {
        Write-Host "   Response Time: $([math]::Round($status.Backend.ResponseTime, 2))ms" -ForegroundColor White
    }
    if ($status.Backend.Error) {
        Write-Host "   Error: $($status.Backend.Error)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🎨 Frontend:" -ForegroundColor Cyan
    Write-Host "   Processes: $($status.Frontend.ProcessCount) $(if($status.Frontend.PIDs) { "($($status.Frontend.PIDs -join ', '))" })" -ForegroundColor White
    Write-Host "   Health: $(if($status.Frontend.IsHealthy) { '✅ HEALTHY' } else { '❌ UNHEALTHY' })" -ForegroundColor $(if($status.Frontend.IsHealthy) { 'Green' } else { 'Red' })
    if ($status.Frontend.Error) {
        Write-Host "   Error: $($status.Frontend.Error)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🌐 URLs:" -ForegroundColor Cyan
    Write-Host "   Frontend:  $($CONFIG.FrontendUrl)" -ForegroundColor White
    Write-Host "   Backend:   $($CONFIG.BackendUrl)" -ForegroundColor White
    Write-Host "   API Docs:  $($CONFIG.BackendUrl)/docs" -ForegroundColor White
    Write-Host "   Admin:     $($CONFIG.BackendUrl)/api/admin/status" -ForegroundColor White
    
    return $status
}

function Save-ProcessInfo {
    param($BackendProcess, $FrontendProcess)
    
    $processInfo = @{
        Timestamp = Get-Date
        Backend = if ($BackendProcess) { 
            @{ PID = $BackendProcess.Id; StartTime = $BackendProcess.StartTime } 
        } else { $null }
        Frontend = if ($FrontendProcess) { 
            @{ PID = $FrontendProcess.Id; StartTime = $FrontendProcess.StartTime } 
        } else { $null }
    }
    
    $processInfo | ConvertTo-Json | Set-Content $CONFIG.PidFile
}

function Start-MonitoringDashboard {
    Write-AppLog "Starting monitoring dashboard..." "INFO"
    
    # Check if the monitoring dashboard script exists
    $monitoringScript = Join-Path $ProjectRoot "scripts\testing\monitoring_dashboard.ps1"
    if (-not (Test-Path $monitoringScript)) {
        Write-AppLog "Monitoring dashboard script not found: $monitoringScript" "ERROR"
        return $null
    }
    
    try {
        # Start the monitoring dashboard in a new window
        $process = Start-Process -FilePath "powershell" -ArgumentList "-File", $monitoringScript, "-RefreshInterval", "10", "-DetailedMode" `
            -WindowStyle Normal -PassThru
        
        Write-AppLog "Monitoring dashboard started with PID: $($process.Id)" "SUCCESS"
        return $process
    }
    catch {
        Write-AppLog "Failed to start monitoring dashboard: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

# Main execution logic
switch ($Action.ToLower()) {
    "start" {
        Write-AppLog "🚀 Starting SocioRAG Application" "INFO"
        
        # Validate environment
        if (-not (Test-Path "backend\app\main.py")) {
            Write-AppLog "Error: Run this from the SocioRAG root directory" "ERROR"
            exit 1
        }
        
        # Clean up logs first
        Cleanup-LogFiles -RetainCount 3
        
        # Start backend
        $backendProcess = Start-BackendProcess
        if (-not $backendProcess) {
            Write-AppLog "Failed to start backend" "ERROR"
            exit 1
        }
        
        # Start frontend
        $frontendProcess = Start-FrontendProcess
        if (-not $frontendProcess) {
            Write-AppLog "Failed to start frontend" "ERROR"
            Stop-SocioRAGServices
            exit 1
        }
        
        # Save process info
        Save-ProcessInfo -BackendProcess $backendProcess -FrontendProcess $frontendProcess
        
        # Start monitoring if requested
        if ($EnableMonitoring) {
            $monitoringProcess = Start-MonitoringDashboard
            if (-not $monitoringProcess) {
                Write-AppLog "Warning: Failed to start monitoring dashboard" "WARNING"
            }
        }
        
        # Wait for services if requested
        if ($WaitForReady) {
            if (-not (Wait-ForServices -TimeoutSeconds $TimeoutSeconds)) {
                Write-AppLog "Services failed to become ready" "ERROR"
                Stop-SocioRAGServices
                exit 1
            }
        }
        
        # Show status
        Get-ServiceStatus | Out-Null
        
        # Open browser unless skipped
        if (-not $SkipBrowser) {
            Write-AppLog "Opening frontend in browser..." "INFO"
            Start-Process $CONFIG.FrontendUrl
        }
        
        Write-AppLog "SocioRAG startup completed successfully!" "SUCCESS"
    }
    
    "stop" {
        Write-AppLog "🛑 Stopping SocioRAG Application" "INFO"
        Stop-SocioRAGServices
        Write-AppLog "SocioRAG shutdown completed" "SUCCESS"
    }
    
    "restart" {
        Write-AppLog "🔄 Restarting SocioRAG Application" "INFO"
        Stop-SocioRAGServices
        Start-Sleep -Seconds 3
        & $MyInvocation.MyCommand.Path -Action "start" -WaitForReady:$WaitForReady -SkipBrowser:$SkipBrowser -EnableMonitoring:$EnableMonitoring -TimeoutSeconds $TimeoutSeconds
    }
      "status" {
        Get-ServiceStatus | Out-Null
    }
    
    "clean" {
        Write-AppLog "🧹 Cleaning up SocioRAG Log Files" "INFO"
        Cleanup-LogFiles -RetainCount 3 -Force
        Write-AppLog "Log cleanup completed" "SUCCESS"
    }
    
    default {
        Write-AppLog "Invalid action: $Action. Use: start, stop, restart, status, or clean" "ERROR"
        exit 1
    }
}
