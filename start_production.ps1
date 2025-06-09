#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Simple SocioRAG Production Startup Script
    
.DESCRIPTION
    Starts both backend and frontend servers with clear logging and monitoring.
    
.PARAMETER Port
    Backend port (default: 8000)
    
.PARAMETER FrontendPort  
    Frontend port (default: 3000)
    
.PARAMETER CleanLogs
    Clean logs before starting
    
.PARAMETER ShowStartupLogs
    Show backend startup logs for debugging
    
.EXAMPLE
    .\start_production.ps1
    .\start_production.ps1 -CleanLogs
    .\start_production.ps1 -Port 8080 -FrontendPort 3001
    .\start_production.ps1 -ShowStartupLogs
#>

param(
    [int]$Port = 8000,
    [int]$FrontendPort = 3000,
    [switch]$CleanLogs,
    [switch]$ShowStartupLogs
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green" 
$InfoColor = "Cyan"
$WarningColor = "Yellow"

# Global variables for process tracking
$BackendProcess = $null
$FrontendProcess = $null
$LogsDir = "logs"

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Color = "White"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp][$Level] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    
    # Also write to main log file
    $logMessage | Out-File -FilePath "$LogsDir\production.log" -Append -Encoding UTF8
}

function Stop-Services {
    Write-Log "Stopping SocioRAG services..." "INFO" $WarningColor
    
    if ($BackendProcess -and !$BackendProcess.HasExited) {
        Write-Log "Stopping backend process (PID: $($BackendProcess.Id))" "INFO" $InfoColor
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if ($FrontendProcess -and !$FrontendProcess.HasExited) {
        Write-Log "Stopping frontend process (PID: $($FrontendProcess.Id))" "INFO" $InfoColor
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Kill any remaining processes
    Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*node*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Log "Services stopped" "SUCCESS" $SuccessColor
}

function Test-Prerequisites {
    Write-Log "Checking prerequisites..." "INFO" $InfoColor
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Log "Python: $pythonVersion" "INFO" $InfoColor
    } catch {
        Write-Log "Python not found" "ERROR" $ErrorColor
        return $false
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>&1
        Write-Log "Node.js: $nodeVersion" "INFO" $InfoColor
    } catch {
        Write-Log "Node.js not found" "ERROR" $ErrorColor
        return $false
    }
    
    # Check if conda/venv is activated
    if ($env:CONDA_DEFAULT_ENV -or $env:VIRTUAL_ENV) {
        Write-Log "Virtual environment active: $($env:CONDA_DEFAULT_ENV)$($env:VIRTUAL_ENV)" "SUCCESS" $SuccessColor
    } else {
        Write-Log "No virtual environment detected. Consider activating one." "WARNING" $WarningColor
    }
    
    return $true
}

function Initialize-Logs {
    if (!(Test-Path $LogsDir)) {
        New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
    }
    
    if ($CleanLogs) {
        Write-Log "Cleaning logs..." "INFO" $InfoColor
        Get-ChildItem -Path $LogsDir -Filter "*.log" | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Log "Logs cleaned" "SUCCESS" $SuccessColor
    }
}

function Start-Backend {
    Write-Log "Starting backend server on port $Port..." "INFO" $InfoColor
    
    # More robust port checking using netstat
    $portUsed = netstat -ano | findstr ":$Port " | findstr "LISTENING"
    if ($portUsed) {
        Write-Log "Port $Port is still in use after cleanup. Attempting to free it..." "WARNING" $WarningColor
        
        # Try to kill the process using the port
        $portProcessIds = netstat -ano | findstr ":$Port " | findstr "LISTENING" | ForEach-Object {
            $_.Trim() -split '\s+' | Select-Object -Last 1
        }
        
        foreach ($pid in $portProcessIds) {
            if ($pid -and $pid -match '^\d+$') {
                Write-Log "Killing process $pid using port $Port" "INFO" $InfoColor
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        }
        
        Start-Sleep -Seconds 3
        
        # Check again
        $portUsed = netstat -ano | findstr ":$Port " | findstr "LISTENING"
        if ($portUsed) {
            Write-Log "Port $Port is still in use. Cannot start backend." "ERROR" $ErrorColor
            Write-Log "Please manually stop the process using port $Port" "ERROR" $ErrorColor
            return $false
        }
    }
    
    try {
        # Start backend with logging
        $backendLogFile = "$LogsDir\backend.log"
        $backendErrorFile = "$LogsDir\backend_error.log"
          # Start backend without stream redirection to avoid process management issues
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "python"
        $processInfo.Arguments = "-m uvicorn backend.app.main:app --host 0.0.0.0 --port $Port --log-level info --access-log"
        $processInfo.WorkingDirectory = $PWD
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        
        # Note: SocioRAG has its own logging to logs/sociorag.log, so we don't need to capture streams
        $script:BackendProcess = [System.Diagnostics.Process]::Start($processInfo)
          Write-Log "Backend started with PID: $($BackendProcess.Id)" "SUCCESS" $SuccessColor
        Write-Log "Backend logs: logs\sociorag.log (application logs)" "INFO" $InfoColor
        return $true
        
    } catch {
        Write-Log "Failed to start backend: $($_.Exception.Message)" "ERROR" $ErrorColor
        return $false
    }
}

function Start-Frontend {
    Write-Log "Starting frontend server on port $FrontendPort..." "INFO" $InfoColor
    
    # More robust port checking using netstat
    $portUsed = netstat -ano | findstr ":$FrontendPort " | findstr "LISTENING"
    if ($portUsed) {
        Write-Log "Port $FrontendPort is still in use after cleanup. Attempting to free it..." "WARNING" $WarningColor
        
        # Try to kill the process using the port
        $portProcessIds = netstat -ano | findstr ":$FrontendPort " | findstr "LISTENING" | ForEach-Object {
            $_.Trim() -split '\s+' | Select-Object -Last 1
        }
        
        foreach ($pid in $portProcessIds) {
            if ($pid -and $pid -match '^\d+$') {
                Write-Log "Killing process $pid using port $FrontendPort" "INFO" $InfoColor
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        }
        
        Start-Sleep -Seconds 3
        
        # Check again
        $portUsed = netstat -ano | findstr ":$FrontendPort " | findstr "LISTENING"
        if ($portUsed) {
            Write-Log "Port $FrontendPort is still in use. Cannot start frontend." "ERROR" $ErrorColor
            Write-Log "Please manually stop the process using port $FrontendPort" "ERROR" $ErrorColor
            return $false
        }
    }
    
    # Check if dependencies are installed
    if (!(Test-Path "ui\node_modules")) {
        Write-Log "Installing frontend dependencies..." "INFO" $InfoColor
        Set-Location ui
        npm install
        Set-Location ..
    }
    
    try {
        # Start frontend with logging
        $frontendLogFile = "$LogsDir\frontend.log"
        $frontendErrorFile = "$LogsDir\frontend_error.log"        # Start frontend without stream redirection to avoid process management issues
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "cmd"
        $processInfo.Arguments = "/c npm run dev -- --port $FrontendPort --host 0.0.0.0"
        $processInfo.WorkingDirectory = Join-Path $PWD "ui"
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        
        $script:FrontendProcess = [System.Diagnostics.Process]::Start($processInfo)
          Write-Log "Frontend started with PID: $($FrontendProcess.Id)" "SUCCESS" $SuccessColor
        Write-Log "Frontend logs: Browser console (React dev server)" "INFO" $InfoColor
        return $true
        
    } catch {
        Write-Log "Failed to start frontend: $($_.Exception.Message)" "ERROR" $ErrorColor
        return $false
    }
}

function Test-Services {
    Write-Log "Testing service health..." "INFO" $InfoColor
    
    # Test backend health with extended timeout for SocioRAG initialization
    $maxRetries = 90  # Increased to 90 (3 minutes total)
    $retryCount = 0
    $backendReady = $false
    
    Write-Log "Waiting for backend to initialize (this may take up to 2 minutes)..." "INFO" $InfoColor
    Write-Log "Backend needs time to load spaCy models and initialize database..." "INFO" $InfoColor
    Start-Sleep -Seconds 15  # Give backend more initial time to start
    
    while ($retryCount -lt $maxRetries -and !$backendReady) {        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/admin/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $backendReady = $true
                Write-Log "Backend health check passed" "SUCCESS" $SuccessColor
            }        } catch {
            $retryCount++
            if ($retryCount -eq $maxRetries) {
                Write-Log "Backend health check failed after $maxRetries attempts (3 minutes)" "ERROR" $ErrorColor
                Write-Log "Backend may still be initializing. Check logs/sociorag.log for details" "WARNING" $WarningColor
                Write-Log "You can try accessing http://localhost:$Port/api/admin/health manually" "INFO" $InfoColor
            } else {
                if ($retryCount % 15 -eq 0) {
                    $elapsed = [math]::Round(($retryCount * 2) / 60, 1)
                    Write-Log "Still waiting for backend... ($elapsed minutes elapsed, max 3 minutes)" "INFO" $InfoColor
                }
                Start-Sleep -Seconds 2
            }
        }
    }
    
    # Test frontend (check if process is running)
    if ($FrontendProcess -and !$FrontendProcess.HasExited) {
        Write-Log "Frontend process is running" "SUCCESS" $SuccessColor
    } else {
        Write-Log "Frontend process is not running" "ERROR" $ErrorColor
    }
      return $backendReady
}

function Show-StartupLogs {
    if ($ShowStartupLogs -and (Test-Path "logs\sociorag.log")) {
        Write-Log "Backend startup logs (last 10 lines):" "INFO" $InfoColor
        Write-Host "----------------------------------------" -ForegroundColor Gray
        Get-Content "logs\sociorag.log" -Tail 10 -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host $_ -ForegroundColor Gray
        }
        Write-Host "----------------------------------------" -ForegroundColor Gray
    }
}

function Show-Status {
    Write-Log "Service Status:" "INFO" $InfoColor
    Write-Log "  Backend:  http://localhost:$Port" "INFO" $InfoColor
    Write-Log "  Frontend: http://localhost:$FrontendPort" "INFO" $InfoColor
    Write-Log "  API Docs: http://localhost:$Port/docs" "INFO" $InfoColor
    Write-Log "" "INFO" $InfoColor    Write-Log "Log Files:" "INFO" $InfoColor
    Write-Log "  Production: $LogsDir\production.log" "INFO" $InfoColor
    Write-Log "  Backend:    $LogsDir\sociorag.log (application logs)" "INFO" $InfoColor
    Write-Log "  Frontend:   Browser console (React dev server)" "INFO" $InfoColor
    Write-Log "" "INFO" $InfoColor
    Write-Log "Commands:" "INFO" $InfoColor
    Write-Log "  View logs: .\view_logs.ps1" "INFO" $InfoColor
    Write-Log "  Stop:      .\stop_production.ps1" "INFO" $InfoColor
    Write-Log "  Or press Ctrl+C to stop services" "INFO" $InfoColor
}

# Register cleanup handler
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-Services
} | Out-Null

# Handle Ctrl+C
$null = Register-ObjectEvent -InputObject ([Console]) -EventName CancelKeyPress -Action {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    Stop-Services
    [Environment]::Exit(0)
}

# Main execution
try {
    Write-Host "SocioRAG Production Startup" -ForegroundColor Green
    Write-Host "===========================" -ForegroundColor Green
      Initialize-Logs
    
    if (!(Test-Prerequisites)) {
        Write-Log "Prerequisites check failed" "ERROR" $ErrorColor
        exit 1
    }
    
    # Stop any existing services before starting new ones
    Write-Log "Checking for existing SocioRAG processes..." "INFO" $InfoColor
    
    # Kill any existing SocioRAG backend processes
    $existingBackend = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*uvicorn*backend.app.main*" -or 
        $_.CommandLine -like "*uvicorn*backend/app/main*" 
    }
    if ($existingBackend) {
        Write-Log "Stopping existing backend processes..." "WARNING" $WarningColor
        $existingBackend | ForEach-Object { 
            Write-Log "Stopping backend process PID: $($_.Id)" "INFO" $InfoColor
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue 
        }
        Start-Sleep -Seconds 2
    }
    
    # Kill any existing frontend processes on our ports
    $existingFrontend = Get-Process node -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*npm*dev*" -or 
        $_.CommandLine -like "*vite*" 
    }
    if ($existingFrontend) {
        Write-Log "Stopping existing frontend processes..." "WARNING" $WarningColor
        $existingFrontend | ForEach-Object { 
            Write-Log "Stopping frontend process PID: $($_.Id)" "INFO" $InfoColor
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue 
        }
        Start-Sleep -Seconds 2
    }
      # Check if ports are still in use after cleanup using netstat
    $backendPortUsed = netstat -ano | findstr ":$Port " | findstr "LISTENING"
    $frontendPortUsed = netstat -ano | findstr ":$FrontendPort " | findstr "LISTENING"
    
    if ($backendPortUsed -or $frontendPortUsed) {
        if ($backendPortUsed) {
            Write-Log "Warning: Port $Port may still be in use. Waiting for release..." "WARNING" $WarningColor
        }
        if ($frontendPortUsed) {
            Write-Log "Warning: Port $FrontendPort may still be in use. Waiting for release..." "WARNING" $WarningColor
        }
        Start-Sleep -Seconds 5
    }
    
    Write-Log "Ready to start services..." "SUCCESS" $SuccessColor
    
    # Start services
    if (!(Start-Backend)) {
        Write-Log "Backend startup failed" "ERROR" $ErrorColor
        exit 1
    }
    
    if (!(Start-Frontend)) {
        Write-Log "Frontend startup failed" "ERROR" $ErrorColor
        Stop-Services
        exit 1
    }
      # Test services
    if (Test-Services) {
        Write-Log "All services started successfully!" "SUCCESS" $SuccessColor
        Show-StartupLogs
        Show-Status
        
        # Keep script running
        Write-Log "Press Ctrl+C to stop all services..." "INFO" $InfoColor
        try {
            while ($true) {
                Start-Sleep -Seconds 5
                
                # Check if processes are still running
                if ($BackendProcess.HasExited) {
                    Write-Log "Backend process has exited" "ERROR" $ErrorColor
                    break
                }
                if ($FrontendProcess.HasExited) {
                    Write-Log "Frontend process has exited" "ERROR" $ErrorColor
                    break
                }
            }
        } catch {
            # Ctrl+C pressed
        }    } else {        Write-Log "Service health checks failed" "ERROR" $ErrorColor
        Show-StartupLogs
        Write-Log "Try running with -ShowStartupLogs for more details or check logs/sociorag.log" "INFO" $InfoColor
        Stop-Services
        exit 1
    }
    
} catch {
    Write-Log "Unexpected error: $($_.Exception.Message)" "ERROR" $ErrorColor
    Stop-Services
    exit 1
} finally {
    Stop-Services
}
