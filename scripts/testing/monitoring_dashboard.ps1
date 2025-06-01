# SocioRAG Real-Time Monitoring Dashboard
# Provides a continuous real-time view of application performance and health

param(
    [int]$RefreshInterval = 5,
    [int]$MaxLogLines = 20,
    [switch]$DetailedMode
)

# Configuration
$BACKEND_URL = "http://127.0.0.1:8000"
$MONITORING_LOG = "logs\monitoring_dashboard_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Ensure logs directory exists
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Color scheme
$Colors = @{
    Header = "Green"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Metric = "White"
    Highlight = "Magenta"
}

function Clear-Dashboard {
    Clear-Host
    $host.UI.RawUI.WindowTitle = "SocioRAG Performance Monitor"
}

function Write-Header {
    param($Title)
    Write-Host "╔══════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Header
    Write-Host "║ $Title".PadRight(77) + "║" -ForegroundColor $Colors.Header
    Write-Host "╚══════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Header
    Write-Host ""
}

function Write-Section {
    param($Title, $Content = @())
    Write-Host "┌─ $Title " + "─" * (75 - $Title.Length) + "┐" -ForegroundColor $Colors.Info
    foreach ($line in $Content) {
        Write-Host "│ $line".PadRight(77) + "│" -ForegroundColor $Colors.Metric
    }
    Write-Host "└" + "─" * 77 + "┘" -ForegroundColor $Colors.Info
    Write-Host ""
}

function Get-SystemHealth {
    try {
        $health = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -TimeoutSec 5
        return @{
            Status = $health.status
            Uptime = [math]::Round($health.uptime / 3600, 2)
            Components = $health.components
            Success = $true
        }
    }
    catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Get-SystemMetrics {
    try {
        $metrics = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/metrics" -TimeoutSec 5
        return @{
            CPU = $metrics.cpu_usage
            Memory = $metrics.memory_usage
            Disk = $metrics.disk_usage
            Database = $metrics.database_stats
            VectorStore = $metrics.vector_store_stats
            Success = $true
        }
    }
    catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Get-LogAnalytics {
    try {
        $errors = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/errors?hours=1" -TimeoutSec 5
        $performance = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/performance?hours=1" -TimeoutSec 5  
        $health = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/health" -TimeoutSec 5
        $stats = Invoke-RestMethod -Uri "$BACKEND_URL/api/logs/stats" -TimeoutSec 5
        
        return @{
            ErrorRate = $errors.error_rate
            TotalErrors = $errors.total_errors
            Performance = $performance
            SystemHealth = $health
            LogStats = $stats
            Success = $true
        }
    }
    catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

function Format-HealthStatus {
    param($Health)
    
    if (-not $Health.Success) {
        return @("❌ Health check failed: $($Health.Error)")
    }
    
    $status = $Health.Status
    $icon = switch ($status) {
        "healthy" { "✅" }
        "degraded" { "⚠️" }
        "unhealthy" { "❌" }
        default { "❓" }
    }
    
    $lines = @(
        "$icon Overall Status: $status",
        "⏱️  Uptime: $($Health.Uptime) hours"
    )
    
    if ($Health.Components) {
        $lines += "📦 Components:"
        foreach ($component in $Health.Components.PSObject.Properties) {
            $comp = $component.Value
            $compIcon = if ($comp.status -eq "healthy") { "✅" } else { "❌" }
            $lines += "   $compIcon $($component.Name): $($comp.status)"
        }
    }
    
    return $lines
}

function Format-SystemMetrics {
    param($Metrics)
    
    if (-not $Metrics.Success) {
        return @("❌ Metrics unavailable: $($Metrics.Error)")
    }
    
    $cpuColor = if ($Metrics.CPU -gt 80) { "🔴" } elseif ($Metrics.CPU -gt 60) { "🟡" } else { "🟢" }
    $memColor = if ($Metrics.Memory.percentage -gt 80) { "🔴" } elseif ($Metrics.Memory.percentage -gt 60) { "🟡" } else { "🟢" }
    $diskColor = if ($Metrics.Disk.percentage -gt 90) { "🔴" } elseif ($Metrics.Disk.percentage -gt 75) { "🟡" } else { "🟢" }
    
    $lines = @(
        "$cpuColor CPU: $($Metrics.CPU)%",
        "$memColor Memory: $($Metrics.Memory.percentage)% ($($Metrics.Memory.used_gb)GB/$($Metrics.Memory.total_gb)GB)",
        "$diskColor Disk: $($Metrics.Disk.percentage)% ($($Metrics.Disk.used_gb)GB/$($Metrics.Disk.total_gb)GB)"
    )
    
    if ($Metrics.Database) {
        $lines += "🗄️  Database:"
        if ($Metrics.Database.entity_count) { $lines += "   📊 Entities: $($Metrics.Database.entity_count)" }
        if ($Metrics.Database.relation_count) { $lines += "   🔗 Relations: $($Metrics.Database.relation_count)" }
        if ($Metrics.Database.documents_count) { $lines += "   📄 Documents: $($Metrics.Database.documents_count)" }
        if ($Metrics.Database.file_size_mb) { $lines += "   💾 DB Size: $($Metrics.Database.file_size_mb)MB" }
    }
    
    if ($Metrics.VectorStore) {
        $lines += "🔍 Vector Store:"
        if ($Metrics.VectorStore.document_count) { $lines += "   📚 Documents: $($Metrics.VectorStore.document_count)" }
        if ($Metrics.VectorStore.storage_size_mb) { $lines += "   💾 Size: $($Metrics.VectorStore.storage_size_mb)MB" }
    }
    
    return $lines
}

function Format-LogAnalytics {
    param($Analytics)
    
    if (-not $Analytics.Success) {
        return @("❌ Analytics unavailable: $($Analytics.Error)")
    }
    
    $errorIcon = if ($Analytics.ErrorRate -gt 0.05) { "🔴" } elseif ($Analytics.ErrorRate -gt 0.01) { "🟡" } else { "🟢" }
    $healthIcon = switch ($Analytics.SystemHealth.status) {
        "healthy" { "🟢" }
        "warning" { "🟡" }
        "critical" { "🔴" }
        default { "❓" }
    }
    
    $lines = @(
        "$errorIcon Error Rate: $([math]::Round($Analytics.ErrorRate * 100, 2))% ($($Analytics.TotalErrors) errors)",
        "$healthIcon System Health: $($Analytics.SystemHealth.status)"
    )
    
    if ($Analytics.Performance.api_performance) {
        $lines += "⚡ API Performance (top endpoints):"
        $sortedEndpoints = $Analytics.Performance.api_performance.PSObject.Properties | 
            Where-Object { $_.Value.avg } | 
            Sort-Object { $_.Value.avg } -Descending | 
            Select-Object -First 3
            
        foreach ($endpoint in $sortedEndpoints) {
            $avg = [math]::Round($endpoint.Value.avg, 1)
            $count = $endpoint.Value.count
            $perfIcon = if ($avg -gt 2000) { "🔴" } elseif ($avg -gt 1000) { "🟡" } else { "🟢" }
            $lines += "   $perfIcon $($endpoint.Name): ${avg}ms ($count req)"
        }
    }
    
    if ($Analytics.LogStats) {
        $lines += "📋 Log Statistics:"
        $lines += "   📊 Total Entries: $($Analytics.LogStats.total_log_files)"
        if ($Analytics.LogStats.total_size_mb) {
            $lines += "   💾 Total Size: $($Analytics.LogStats.total_size_mb)MB"
        }
    }
    
    return $lines
}

function Get-RecentLogEntries {
    param($MaxLines = 10)
    
    # Get recent entries from the main log file
    $logFile = "logs\sociorag_debug.log"
    if (Test-Path $logFile) {
        try {
            $lines = Get-Content $logFile -Tail $MaxLines -ErrorAction SilentlyContinue
            return $lines | ForEach-Object {
                $line = $_
                if ($line -match "ERROR|CRITICAL") { "🔴 $line" }
                elseif ($line -match "WARNING") { "🟡 $line" }
                elseif ($line -match "INFO") { "🔵 $line" }
                else { "⚪ $line" }
            }
        }
        catch {
            return @("❌ Error reading log file: $($_.Exception.Message)")
        }
    }
    else {
        return @("📋 No log file found at $logFile")
    }
}

function Show-Dashboard {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Clear-Dashboard
    Write-Header "SocioRAG Real-Time Performance Dashboard - $timestamp"
    
    # Collect all data
    Write-Host "🔄 Collecting metrics..." -ForegroundColor $Colors.Info
    $health = Get-SystemHealth
    $metrics = Get-SystemMetrics  
    $analytics = Get-LogAnalytics
    
    Clear-Dashboard
    Write-Header "SocioRAG Real-Time Performance Dashboard - $timestamp"
    
    # Display system health
    Write-Section "System Health" (Format-HealthStatus $health)
    
    # Display system metrics
    Write-Section "System Metrics" (Format-SystemMetrics $metrics)
    
    # Display log analytics
    Write-Section "Log Analytics (Last Hour)" (Format-LogAnalytics $analytics)
    
    # Display recent log entries if in detailed mode
    if ($DetailedMode) {
        $recentLogs = Get-RecentLogEntries -MaxLines $MaxLogLines
        Write-Section "Recent Log Entries" $recentLogs
    }
    
    # Display instructions
    $instructions = @(
        "🔄 Refresh Interval: $RefreshInterval seconds",
        "💡 Press Ctrl+C to stop monitoring",
        "🌐 Frontend: http://localhost:5173",
        "🔧 Backend: $BACKEND_URL",
        "📚 API Docs: $BACKEND_URL/docs"
    )
    Write-Section "Instructions" $instructions
    
    # Log to file
    $logEntry = "[$timestamp] Health: $($health.Status), CPU: $($metrics.CPU)%, Memory: $($metrics.Memory.percentage)%, Errors: $($analytics.TotalErrors)"
    Add-Content -Path $MONITORING_LOG -Value $logEntry -ErrorAction SilentlyContinue
}

# Main monitoring loop
Write-Host "🚀 Starting SocioRAG Real-Time Performance Dashboard..." -ForegroundColor $Colors.Success
Write-Host "⏱️  Refresh interval: $RefreshInterval seconds" -ForegroundColor $Colors.Info
if ($DetailedMode) {
    Write-Host "📋 Detailed mode enabled (showing recent log entries)" -ForegroundColor $Colors.Info
}
Write-Host "📁 Monitoring log: $MONITORING_LOG" -ForegroundColor $Colors.Info
Write-Host ""

# Test initial connection
try {
    $testResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/admin/health" -TimeoutSec 5
    Write-Host "✅ Successfully connected to SocioRAG backend" -ForegroundColor $Colors.Success
}
catch {
    Write-Host "❌ Cannot connect to SocioRAG backend at $BACKEND_URL" -ForegroundColor $Colors.Error
    Write-Host "💡 Please ensure the application is running first" -ForegroundColor $Colors.Warning
    Write-Host "🚀 You can start it with: .\quick_start.ps1" -ForegroundColor $Colors.Info
    exit 1
}

Write-Host "🔄 Starting monitoring loop..." -ForegroundColor $Colors.Info
Start-Sleep -Seconds 2

try {
    while ($true) {
        Show-Dashboard
        Start-Sleep -Seconds $RefreshInterval
    }
}
catch {
    Write-Host ""
    Write-Host "🛑 Monitoring stopped." -ForegroundColor $Colors.Warning
    Write-Host "📁 Monitoring log saved to: $MONITORING_LOG" -ForegroundColor $Colors.Info
    Write-Host "✨ Thank you for monitoring SocioRAG!" -ForegroundColor $Colors.Success
}
