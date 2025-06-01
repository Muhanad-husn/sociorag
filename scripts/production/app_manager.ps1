# SocioRAG Application Manager
# Coordinates backend and frontend startup with proper monitoring integration
# Designed to work seamlessly with performance testing and monitoring scripts

param(
    [ValidateSet("start", "stop", "restart", "status")]
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
    LogFile = "logs\app_manager_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
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
    param($Url, $TimeoutSec = 5)
    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec $TimeoutSec -ErrorAction Stop
        return @{
            IsHealthy = $true
            Response = $response
            ResponseTime = (Measure-Command { 
                Invoke-RestMethod -Uri $Url -TimeoutSec $TimeoutSec 
            }).TotalMilliseconds
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
    }
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "backend.app.main" `
            -WorkingDirectory $PWD -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput "logs\backend_output.log" `
            -RedirectStandardError "logs\backend_error.log"
        
        Write-AppLog "Backend started with PID: $($process.Id)" "SUCCESS"
        return $process
    }
    catch {
        Write-AppLog "Failed to start backend: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

function Start-FrontendProcess {
    Write-AppLog "Starting frontend process..." "INFO"
    
    # Check if already running
    $existingFrontend = Get-Process -Name "node" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*dev*" }
    
    if ($existingFrontend) {
        Write-AppLog "Frontend already running (PID: $($existingFrontend.Id))" "WARNING"
        return $existingFrontend
    }
    
    if (-not (Test-Path "ui")) {
        Write-AppLog "Frontend directory 'ui' not found" "ERROR"
        return $null
    }
      try {
        $packageManager = if (Get-Command pnpm -ErrorAction SilentlyContinue) { "pnpm" } else { "npm" }
        
        $process = Start-Process -FilePath $packageManager -ArgumentList "run", "dev" `
            -WorkingDirectory "ui" -PassThru -WindowStyle Hidden
        
        Write-AppLog "Frontend started with PID: $($process.Id) using $packageManager" "SUCCESS"
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
            $frontendHealth = Test-ServiceHealth -Url $CONFIG.FrontendUrl
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
    $frontendProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | 
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
    $frontendProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*dev*" }
    
    # Check health
    $backendHealth = Test-ServiceHealth -Url "$($CONFIG.BackendUrl)/api/admin/health"
    $frontendHealth = Test-ServiceHealth -Url $CONFIG.FrontendUrl
    
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

# Main execution logic
switch ($Action.ToLower()) {
    "start" {
        Write-AppLog "🚀 Starting SocioRAG Application" "INFO"
        
        # Validate environment
        if (-not (Test-Path "backend\app\main.py")) {
            Write-AppLog "Error: Run this from the SocioRAG root directory" "ERROR"
            exit 1
        }
        
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
    
    default {
        Write-AppLog "Invalid action: $Action. Use: start, stop, restart, or status" "ERROR"
        exit 1
    }
}
