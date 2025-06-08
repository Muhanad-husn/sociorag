# SocioRAG Log Viewer Script
# This script provides a convenient way to view different log files

param(
    [ValidateSet("app", "errors", "structured", "manager", "all")]
    [string]$LogType = "app",
    
    [int]$Lines = 50
)

$logs = @{
    "app" = "logs\sociorag_application.log"
    "errors" = "logs\sociorag_errors.log"
    "structured" = "logs\sociorag_structured.log"
    "manager" = "logs\app_manager.log"
}

function Show-LogFile {
    param(
        [string]$LogPath,
        [string]$Title,
        [int]$Lines
    )
    
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
    
    if (Test-Path $LogPath) {
        if ((Get-Item $LogPath).Length -eq 0) {
            Write-Host "Log file is empty" -ForegroundColor Yellow
        } else {            Write-Host "Showing last $Lines lines of $LogPath" -ForegroundColor Gray
            Get-Content -Path $LogPath -Tail $Lines
        }
    } else {
        Write-Host "Log file not found: $LogPath" -ForegroundColor Red
    }
}

if ($LogType -eq "all") {
    # Show all logs
    foreach ($key in $logs.Keys) {
        Show-LogFile -LogPath $logs[$key] -Title $key.ToUpper() -Lines $Lines
    }
} else {
    # Show specific log
    Show-LogFile -LogPath $logs[$LogType] -Title $LogType.ToUpper() -Lines $Lines
}

Write-Host "`nTo view a specific log file, use: .\view_logs.ps1 -LogType [app|errors|structured|manager|all]" -ForegroundColor Gray
Write-Host "To change the number of lines, use: .\view_logs.ps1 -Lines 100" -ForegroundColor Gray
