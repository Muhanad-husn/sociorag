#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Simple SocioRAG Production Stop Script
    
.DESCRIPTION
    Stops all SocioRAG services (backend and frontend)
    
.EXAMPLE
    .\stop.ps1
#>

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green" 
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Color = "White"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp][$Level] $Message"
    Write-Host $logMessage -ForegroundColor $Color
}

function Stop-SocioRAGServices {
    Write-Log "Stopping SocioRAG services..." "INFO" $WarningColor
    
    $processesKilled = 0
    
    # Stop uvicorn/FastAPI processes
    Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*" } | ForEach-Object {
        Write-Log "Stopping backend process (PID: $($_.Id))" "INFO" $InfoColor
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $processesKilled++
    }
    
    # Stop Node.js/Vite processes
    Get-Process | Where-Object { $_.ProcessName -like "*node*" -and $_.CommandLine -like "*vite*" } | ForEach-Object {
        Write-Log "Stopping frontend process (PID: $($_.Id))" "INFO" $InfoColor
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $processesKilled++
    }
    
    # Alternative approach - kill processes by port
    try {
        # Kill process on port 8000 (backend)
        $backendProcess = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        if ($backendProcess) {
            Stop-Process -Id $backendProcess -Force -ErrorAction SilentlyContinue
            Write-Log "Stopped process using port 8000" "INFO" $InfoColor
            $processesKilled++
        }
        
        # Kill process on port 3000 (frontend)
        $frontendProcess = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        if ($frontendProcess) {
            Stop-Process -Id $frontendProcess -Force -ErrorAction SilentlyContinue
            Write-Log "Stopped process using port 3000" "INFO" $InfoColor
            $processesKilled++
        }
    } catch {
        # Ignore errors - processes might not exist
    }
      # Clean up any remaining Python or Node processes related to SocioRAG
    Get-Process | Where-Object { 
        ($_.ProcessName -eq "python" -or $_.ProcessName -eq "node") -and 
        ($_.CommandLine -like "*sociorag*" -or $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*backend.app.main*")
    } | ForEach-Object {
        Write-Log "Cleaning up remaining process (PID: $($_.Id))" "INFO" $InfoColor
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $processesKilled++
    }
    
    # Additional check for any Python process running backend.app.main
    Get-WmiObject Win32_Process | Where-Object { 
        $_.Name -eq "python.exe" -and $_.CommandLine -like "*backend.app.main*"
    } | ForEach-Object {
        Write-Log "Found SocioRAG backend process (PID: $($_.ProcessId))" "INFO" $InfoColor
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $processesKilled++
    }
      if ($processesKilled -gt 0) {
        Write-Log "Stopped $processesKilled process(es)" "SUCCESS" $SuccessColor
    } else {
        Write-Log "No SocioRAG processes found to stop" "INFO" $InfoColor
    }
      # Clean up any background jobs
    Get-Job | Stop-Job -PassThru | Remove-Job -ErrorAction SilentlyContinue
    
    Write-Log "SocioRAG shutdown completed" "SUCCESS" $SuccessColor
}

# Main execution
try {
    Write-Host "Stop SocioRAG Production" -ForegroundColor Yellow
    Write-Host "========================" -ForegroundColor Yellow
    
    Stop-SocioRAGServices
    
} catch {
    Write-Log "Error during shutdown: $($_.Exception.Message)" "ERROR" $ErrorColor
    exit 1
}
