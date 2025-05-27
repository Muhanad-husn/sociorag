# SocioRAG Log Viewer
# View and analyze SocioRAG application logs

param(
    [string]$LogType = "main",     # main, errors, debug
    [int]$Lines = 100,             # Number of recent lines to show
    [string]$Filter = "",          # Filter log entries containing this text
    [string]$Since = "",           # Show logs since this time (e.g., "2024-05-27 10:00")
    [switch]$Stats,                # Show log statistics
    [switch]$Follow                # Follow log in real-time (same as monitor_logs.ps1 -Tail)
)

Write-Host "📋 SocioRAG Log Viewer" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""

# Determine log file
$logFile = switch ($LogType.ToLower()) {
    "main" { "logs\sociorag.log" }
    "errors" { "logs\sociorag_errors.log" }
    "debug" { "logs\sociorag_debug.log" }
    default { 
        Write-Host "❌ Invalid log type: $LogType" -ForegroundColor Red
        Write-Host "Valid types: main, errors, debug" -ForegroundColor Yellow
        exit 1
    }
}

$logPath = Join-Path $PSScriptRoot $logFile

Write-Host "📁 Log file: $logPath" -ForegroundColor Cyan
Write-Host "📊 Log type: $LogType" -ForegroundColor Cyan

# Check if log file exists
if (-not (Test-Path $logPath)) {
    Write-Host "❌ Log file not found: $logPath" -ForegroundColor Red
    Write-Host "The application may not have been started yet." -ForegroundColor Yellow
    exit 1
}

# Get file info
$logInfo = Get-Item $logPath
Write-Host "📅 Last modified: $($logInfo.LastWriteTime)" -ForegroundColor Gray
Write-Host "📏 File size: $([math]::Round($logInfo.Length / 1KB, 2)) KB" -ForegroundColor Gray
Write-Host ""

# Show statistics if requested
if ($Stats) {
    Write-Host "📊 Log Statistics:" -ForegroundColor Yellow
    Write-Host "─────────────────" -ForegroundColor Gray
    
    $content = Get-Content $logPath
    $totalLines = $content.Count
    $errorLines = ($content | Where-Object { $_ -match "ERROR" }).Count
    $warningLines = ($content | Where-Object { $_ -match "WARNING" }).Count
    $infoLines = ($content | Where-Object { $_ -match "INFO" }).Count
    $debugLines = ($content | Where-Object { $_ -match "DEBUG" }).Count
    
    Write-Host "Total lines: $totalLines" -ForegroundColor White
    Write-Host "ERROR entries: $errorLines" -ForegroundColor Red
    Write-Host "WARNING entries: $warningLines" -ForegroundColor Yellow
    Write-Host "INFO entries: $infoLines" -ForegroundColor Green
    Write-Host "DEBUG entries: $debugLines" -ForegroundColor Gray
    Write-Host ""
    
    if ($errorLines -gt 0) {
        Write-Host "Recent errors:" -ForegroundColor Red
        $content | Where-Object { $_ -match "ERROR" } | Select-Object -Last 5 | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Red
        }
        Write-Host ""
    }
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
    elseif ($line -match "INFO.*Starting|INFO.*Startup|INFO.*Ready|INFO.*Initialized") {
        Write-Host $line -ForegroundColor Green
    }
    elseif ($line -match "DEBUG") {
        Write-Host $line -ForegroundColor Gray
    }
    else {
        Write-Host $line -ForegroundColor White
    }
}

# Filter by time if specified
$contentToShow = Get-Content $logPath

if ($Since) {
    try {
        $sinceDate = [DateTime]::Parse($Since)
        Write-Host "🕐 Filtering logs since: $sinceDate" -ForegroundColor Cyan
        
        $contentToShow = $contentToShow | Where-Object {
            if ($_ -match "^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}") {
                $logDate = [DateTime]::Parse($_.Substring(0, 19))
                return $logDate -gt $sinceDate
            }
            return $true  # Include lines without timestamps
        }
    }
    catch {
        Write-Host "❌ Invalid date format: $Since" -ForegroundColor Red
        Write-Host "Use format: 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'" -ForegroundColor Yellow
        exit 1
    }
}

# Filter by text if specified
if ($Filter) {
    Write-Host "🔍 Filtering for: '$Filter'" -ForegroundColor Cyan
    $contentToShow = $contentToShow | Where-Object { $_ -match [regex]::Escape($Filter) }
}

# Follow mode (real-time)
if ($Follow) {
    Write-Host "🔄 Following log in real-time (press Ctrl+C to stop):" -ForegroundColor Cyan
    Write-Host "────────────────────────────────────────────────────" -ForegroundColor Gray
    
    # Show recent lines first
    $contentToShow | Select-Object -Last $Lines | ForEach-Object {
        Format-LogLine $_
    }
    
    # Then follow new entries
    Get-Content $logPath -Wait -Tail 0 | ForEach-Object {
        $line = $_
        $include = $true
        
        # Apply filters
        if ($Filter -and $line -notmatch [regex]::Escape($Filter)) {
            $include = $false
        }
        
        if ($Since -and $include) {
            try {
                $sinceDate = [DateTime]::Parse($Since)
                if ($line -match "^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}") {
                    $logDate = [DateTime]::Parse($line.Substring(0, 19))
                    if ($logDate -le $sinceDate) {
                        $include = $false
                    }
                }
            }
            catch {
                # Include lines we can't parse
            }
        }
        
        if ($include) {
            Format-LogLine $line
        }
    }
}
else {
    # Static view
    $totalEntries = $contentToShow.Count
    $showLines = [math]::Min($Lines, $totalEntries)
    
    Write-Host "📋 Showing last $showLines of $totalEntries log entries:" -ForegroundColor Cyan
    Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray
    
    $contentToShow | Select-Object -Last $showLines | ForEach-Object {
        Format-LogLine $_
    }
    
    if ($totalEntries -gt $Lines) {
        Write-Host ""
        Write-Host "... ($($totalEntries - $Lines) more entries available)" -ForegroundColor Gray
        Write-Host "Use -Lines parameter to show more, or -Follow to monitor in real-time" -ForegroundColor Gray
    }
}
