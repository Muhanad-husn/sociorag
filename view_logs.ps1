#!/usr/bin/env pwsh
<#
.SYNOPSIS
    SocioRAG Log Viewer Script
    
.DESCRIPTION
    Provides a convenient way to view different log files
    
.PARAMETER LogType
    Type of log to view: production, backend, frontend, backend_error, frontend_error, app, errors, structured, manager, all
    
.PARAMETER Lines
    Number of lines to show (default: 50)
    
.PARAMETER Follow
    Follow the log file (like tail -f)
    
.EXAMPLE
    .\view_logs.ps1
    .\view_logs.ps1 -LogType backend
    .\view_logs.ps1 -LogType production -Lines 100
    .\view_logs.ps1 -LogType backend -Follow
#>

param(
    [ValidateSet("production", "backend", "frontend", "backend_error", "frontend_error", "app", "errors", "structured", "manager", "all")]
    [string]$LogType = "production",
    
    [int]$Lines = 50,
    
    [switch]$Follow
)

# Color definitions
$InfoColor = "Cyan"
$ErrorColor = "Red"
$WarningColor = "Yellow"
$SuccessColor = "Green"

$logs = @{
    "production" = "logs\production.log"
    "backend" = "logs\backend.log"
    "frontend" = "logs\frontend.log"
    "backend_error" = "logs\backend_error.log"
    "frontend_error" = "logs\frontend_error.log"
    "app" = "logs\sociorag_application.log"
    "errors" = "logs\sociorag_errors.log"
    "structured" = "logs\sociorag_structured.log"
    "manager" = "logs\app_manager.log"
}

function Show-LogFile {
    param(
        [string]$LogPath,
        [string]$Title,
        [int]$Lines,
        [bool]$FollowMode = $false
    )
    
    Write-Host "`n=== $Title ===" -ForegroundColor $InfoColor
    
    if (Test-Path $LogPath) {
        $fileInfo = Get-Item $LogPath
        if ($fileInfo.Length -eq 0) {
            Write-Host "Log file is empty" -ForegroundColor $WarningColor
        } else {
            Write-Host "File: $LogPath (Size: $([math]::Round($fileInfo.Length/1KB, 2)) KB)" -ForegroundColor Gray
            
            if ($FollowMode) {
                Write-Host "Following log file (Press Ctrl+C to stop)..." -ForegroundColor $InfoColor
                Get-Content -Path $LogPath -Tail $Lines -Wait
            } else {
                Write-Host "Showing last $Lines lines:" -ForegroundColor Gray
                Get-Content -Path $LogPath -Tail $Lines
            }
        }
    } else {
        Write-Host "Log file not found: $LogPath" -ForegroundColor $ErrorColor
    }
}

function Show-LogSummary {
    Write-Host "`nLog Files Summary:" -ForegroundColor $InfoColor
    Write-Host "=====================" -ForegroundColor $InfoColor
    
    foreach ($key in $logs.Keys | Sort-Object) {
        $logPath = $logs[$key]
        if (Test-Path $logPath) {
            $fileInfo = Get-Item $logPath
            $size = [math]::Round($fileInfo.Length/1KB, 2)
            $lastWrite = $fileInfo.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            Write-Host "  $key".PadRight(15) ": $size KB (Last: $lastWrite)" -ForegroundColor White
        } else {
            Write-Host "  $key".PadRight(15) ": Not found" -ForegroundColor $ErrorColor
        }
    }
}

# Main execution
try {
    Write-Host "SocioRAG Log Viewer" -ForegroundColor $SuccessColor
    Write-Host "======================" -ForegroundColor $SuccessColor
    
    if ($LogType -eq "all") {
        # Show summary first
        Show-LogSummary
        
        # Show all logs
        foreach ($key in $logs.Keys | Sort-Object) {
            Show-LogFile -LogPath $logs[$key] -Title "$($key.ToUpper()) LOG" -Lines $Lines -FollowMode $false
        }
    } else {
        # Show specific log
        if ($logs.ContainsKey($LogType)) {
            Show-LogFile -LogPath $logs[$LogType] -Title "$($LogType.ToUpper()) LOG" -Lines $Lines -FollowMode $Follow
        } else {
            Write-Host "Unknown log type: $LogType" -ForegroundColor $ErrorColor
            exit 1
        }
    }
    
} catch {
    Write-Host "Error viewing logs: $($_.Exception.Message)" -ForegroundColor $ErrorColor
    exit 1
}

Write-Host "`nUsage Tips:" -ForegroundColor $InfoColor
Write-Host "  View specific log: .\view_logs.ps1 -LogType [production|backend|frontend|backend_error|frontend_error|app|errors|structured|manager|all]" -ForegroundColor Gray
Write-Host "  Change lines:      .\view_logs.ps1 -Lines 100" -ForegroundColor Gray
Write-Host "  Follow mode:       .\view_logs.ps1 -LogType backend -Follow" -ForegroundColor Gray
