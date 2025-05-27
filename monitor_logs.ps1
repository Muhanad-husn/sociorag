# SocioRAG Log Monitor
# Real-time log monitoring script for Windows PowerShell

param(
    [string]$LogFile = "logs\sociorag.log",
    [string]$LogLevel = "all",
    [switch]$Tail,
    [switch]$Errors,
    [switch]$Debug,
    [int]$Lines = 50
)

Write-Host "🔍 SocioRAG Log Monitor" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

# Determine which log file to monitor
$logPath = Join-Path $PSScriptRoot $LogFile

if ($Errors) {
    $logPath = Join-Path $PSScriptRoot "logs\sociorag_errors.log"
    Write-Host "📋 Monitoring: Error logs only" -ForegroundColor Red
}
elseif ($Debug) {
    $logPath = Join-Path $PSScriptRoot "logs\sociorag_debug.log"
    Write-Host "📋 Monitoring: Debug logs" -ForegroundColor Yellow
}
else {
    Write-Host "📋 Monitoring: Main application logs" -ForegroundColor Cyan
}

Write-Host "📁 Log file: $logPath" -ForegroundColor Gray
Write-Host ""

# Check if log file exists
if (-not (Test-Path $logPath)) {
    Write-Host "⚠️  Log file not found: $logPath" -ForegroundColor Yellow
    Write-Host "The backend server may not be running yet." -ForegroundColor Yellow
    Write-Host "Waiting for log file to be created..." -ForegroundColor Yellow
    
    # Wait for log file to be created
    while (-not (Test-Path $logPath)) {
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "✅ Log file found! Starting monitor..." -ForegroundColor Green
    Start-Sleep -Seconds 1
}

# Function to colorize log output
function Format-LogLine {
    param([string]$line)
    
    if ($line -match "ERROR") {
        Write-Host $line -ForegroundColor Red
    }
    elseif ($line -match "WARNING") {
        Write-Host $line -ForegroundColor Yellow
    }
    elseif ($line -match "INFO.*Starting|INFO.*Startup|INFO.*Ready") {
        Write-Host $line -ForegroundColor Green
    }
    elseif ($line -match "DEBUG") {
        Write-Host $line -ForegroundColor Gray
    }
    else {
        Write-Host $line -ForegroundColor White
    }
}

# Show recent log entries
if ($Lines -gt 0) {
    Write-Host "📚 Recent log entries (last $Lines lines):" -ForegroundColor Cyan
    Write-Host "─────────────────────────────────────────" -ForegroundColor Gray
    
    try {
        Get-Content $logPath -Tail $Lines | ForEach-Object {
            Format-LogLine $_
        }
    }
    catch {
        Write-Host "Could not read initial log content: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🔄 Live monitoring (press Ctrl+C to stop):" -ForegroundColor Cyan
    Write-Host "──────────────────────────────────────────" -ForegroundColor Gray
}

# Real-time monitoring
if ($Tail) {
    try {
        Get-Content $logPath -Wait -Tail 0 | ForEach-Object {
            Format-LogLine $_
        }
    }
    catch {
        Write-Host "Error monitoring log file: $_" -ForegroundColor Red
    }
}
else {
    # Alternative method using FileSystemWatcher for better performance
    try {
        $watcher = New-Object System.IO.FileSystemWatcher
        $watcher.Path = Split-Path $logPath -Parent
        $watcher.Filter = Split-Path $logPath -Leaf
        $watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite
        $watcher.EnableRaisingEvents = $true
        
        $action = {
            Start-Sleep -Milliseconds 100  # Small delay to ensure file is written
            try {
                $newLines = Get-Content $logPath -Tail 10
                foreach ($line in $newLines) {
                    if ($line) {
                        Format-LogLine $line
                    }
                }
            }
            catch {
                # Ignore read errors during file updates
            }
        }
        
        Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
        
        Write-Host "✅ Log monitor active. Press Ctrl+C to stop." -ForegroundColor Green
        
        # Keep the script running
        try {
            while ($true) {
                Start-Sleep -Seconds 1
            }
        }
        finally {
            $watcher.EnableRaisingEvents = $false
            $watcher.Dispose()
            Get-EventSubscriber | Unregister-Event
        }
    }
    catch {
        Write-Host "Error setting up file watcher: $_" -ForegroundColor Red
        Write-Host "Falling back to basic tail mode..." -ForegroundColor Yellow
        
        Get-Content $logPath -Wait -Tail 0 | ForEach-Object {
            Format-LogLine $_
        }
    }
}
