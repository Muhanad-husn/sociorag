# SocioRAG Management Utility
# Manage SocioRAG processes, logs, and monitoring

param(
    [string]$Action = "help",  # help, status, stop, clean-logs, restart
    [switch]$Force             # Force actions without confirmation
)

Write-Host "🔧 SocioRAG Management Utility" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

function Show-Help {
    Write-Host "Available Actions:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  status      - Show running processes and log status" -ForegroundColor White
    Write-Host "  stop        - Stop all SocioRAG processes" -ForegroundColor White
    Write-Host "  clean-logs  - Clean old log files" -ForegroundColor White
    Write-Host "  restart     - Stop processes and restart with monitoring" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Force      - Skip confirmation prompts" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\manage.ps1 status" -ForegroundColor Gray
    Write-Host "  .\manage.ps1 stop" -ForegroundColor Gray
    Write-Host "  .\manage.ps1 clean-logs -Force" -ForegroundColor Gray
    Write-Host "  .\manage.ps1 restart" -ForegroundColor Gray
}

function Show-Status {
    Write-Host "🔍 System Status:" -ForegroundColor Cyan
    Write-Host "───────────────" -ForegroundColor Gray
    
    # Check for Python processes (backend)
    $pythonProcesses = Get-Process | Where-Object { 
        $_.ProcessName -like "*python*" -and 
        $_.CommandLine -like "*backend.app.main*" 
    } -ErrorAction SilentlyContinue
    
    if ($pythonProcesses) {
        Write-Host "✅ Backend processes running:" -ForegroundColor Green
        foreach ($proc in $pythonProcesses) {
            Write-Host "   PID: $($proc.Id), CPU: $($proc.CPU)s, Memory: $([math]::Round($proc.WorkingSet / 1MB, 1))MB" -ForegroundColor White
        }
    } else {
        Write-Host "❌ No backend processes found" -ForegroundColor Red
    }
    
    # Check for Node processes (frontend)
    $nodeProcesses = Get-Process | Where-Object { 
        $_.ProcessName -like "*node*" -or $_.ProcessName -like "*pnpm*"
    } -ErrorAction SilentlyContinue
    
    if ($nodeProcesses) {
        Write-Host "✅ Frontend processes running:" -ForegroundColor Green
        foreach ($proc in $nodeProcesses) {
            Write-Host "   PID: $($proc.Id), Name: $($proc.ProcessName)" -ForegroundColor White
        }
    } else {
        Write-Host "❌ No frontend processes found" -ForegroundColor Yellow
    }
    
    Write-Host ""
    
    # Check log files
    Write-Host "📋 Log Status:" -ForegroundColor Cyan
    Write-Host "─────────────" -ForegroundColor Gray
    
    $logsDir = "logs"
    if (Test-Path $logsDir) {
        $logFiles = @(
            @{Name = "Main Log"; Path = "logs\sociorag.log"},
            @{Name = "Error Log"; Path = "logs\sociorag_errors.log"},
            @{Name = "Debug Log"; Path = "logs\sociorag_debug.log"}
        )
        
        foreach ($logFile in $logFiles) {            if (Test-Path $logFile.Path) {
                $file = Get-Item $logFile.Path
                $size = [math]::Round($file.Length / 1KB, 1)
                $age = [math]::Round(((Get-Date) - $file.LastWriteTime).TotalMinutes, 1)
                Write-Host "✅ $($logFile.Name): ${size}KB, updated ${age}m ago" -ForegroundColor Green
            } else {
                Write-Host "❌ $($logFile.Name): Not found" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "❌ Logs directory not found" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Check ports
    Write-Host "🌐 Port Status:" -ForegroundColor Cyan
    Write-Host "──────────────" -ForegroundColor Gray
    
    $ports = @(8000, 5173)
    foreach ($port in $ports) {
        $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            $serviceName = if ($port -eq 8000) { "Backend API" } else { "Frontend Dev Server" }
            Write-Host "✅ $serviceName listening on port $port" -ForegroundColor Green
        } else {
            $serviceName = if ($port -eq 8000) { "Backend API" } else { "Frontend Dev Server" }
            Write-Host "❌ $serviceName not listening on port $port" -ForegroundColor Red
        }
    }
}

function Stop-Processes {
    Write-Host "🛑 Stopping SocioRAG Processes:" -ForegroundColor Yellow
    Write-Host "──────────────────────────────" -ForegroundColor Gray
    
    if (-not $Force) {
        $confirm = Read-Host "Are you sure you want to stop all SocioRAG processes? (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "Operation cancelled" -ForegroundColor Yellow
            return
        }
    }
    
    # Stop Python processes
    $pythonProcesses = Get-Process | Where-Object { 
        $_.ProcessName -like "*python*" -and 
        $_.CommandLine -like "*backend*" 
    } -ErrorAction SilentlyContinue
    
    foreach ($proc in $pythonProcesses) {
        try {
            Write-Host "Stopping backend process (PID: $($proc.Id))..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force
            Write-Host "✅ Backend process stopped" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to stop backend process: $_" -ForegroundColor Red
        }
    }
    
    # Stop Node processes related to our project
    $nodeProcesses = Get-Process | Where-Object { 
        $_.ProcessName -like "*node*" -and 
        $_.CommandLine -like "*vite*" 
    } -ErrorAction SilentlyContinue
    
    foreach ($proc in $nodeProcesses) {
        try {
            Write-Host "Stopping frontend process (PID: $($proc.Id))..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force
            Write-Host "✅ Frontend process stopped" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to stop frontend process: $_" -ForegroundColor Red
        }
    }
    
    Write-Host "🏁 Process shutdown complete" -ForegroundColor Green
}

function Clean-Logs {
    Write-Host "🧹 Cleaning Log Files:" -ForegroundColor Yellow
    Write-Host "─────────────────────" -ForegroundColor Gray
    
    if (-not (Test-Path "logs")) {
        Write-Host "No logs directory found" -ForegroundColor Yellow
        return
    }
    
    # Show current log status
    $logFiles = Get-ChildItem "logs" -File
    $totalSize = ($logFiles | Measure-Object Length -Sum).Sum
    
    Write-Host "Current logs: $($logFiles.Count) files, $([math]::Round($totalSize / 1MB, 2))MB total" -ForegroundColor White
    
    if (-not $Force) {
        $confirm = Read-Host "Clean old log files? This will remove rotated logs (.log.1, .log.2, etc.) (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "Operation cancelled" -ForegroundColor Yellow
            return
        }
    }
    
    # Remove rotated log files
    $cleanedFiles = 0
    $cleanedSize = 0
    
    Get-ChildItem "logs" -Filter "*.log.*" | ForEach-Object {
        $cleanedSize += $_.Length
        $cleanedFiles++
        Remove-Item $_.FullName -Force
        Write-Host "Removed: $($_.Name)" -ForegroundColor Gray
    }
    
    if ($cleanedFiles -gt 0) {
        Write-Host "✅ Cleaned $cleanedFiles files, freed $([math]::Round($cleanedSize / 1MB, 2))MB" -ForegroundColor Green
    } else {
        Write-Host "✅ No old log files to clean" -ForegroundColor Green
    }
}

function Restart-Application {
    Write-Host "🔄 Restarting SocioRAG:" -ForegroundColor Yellow
    Write-Host "──────────────────────" -ForegroundColor Gray
    
    # Stop processes first
    Stop-Processes
    
    Write-Host ""
    Write-Host "Waiting 3 seconds for processes to fully stop..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Start with monitoring
    Write-Host "Starting SocioRAG with monitoring..." -ForegroundColor Green
    .\start_with_monitoring.ps1 -Monitor
}

# Main action handler
switch ($Action.ToLower()) {
    "help" { Show-Help }
    "status" { Show-Status }
    "stop" { Stop-Processes }
    "clean-logs" { Clean-Logs }
    "restart" { Restart-Application }
    default {
        Write-Host "❌ Unknown action: $Action" -ForegroundColor Red
        Write-Host "Use 'help' to see available actions" -ForegroundColor Yellow
    }
}
