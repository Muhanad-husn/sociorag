# Enhanced SocioRAG Startup Script with Monitoring
# Provides options for monitoring backend logs during startup

param(
    [switch]$Monitor,           # Monitor logs in real-time
    [switch]$ShowBackend,       # Show backend window (don't hide it)
    [switch]$DebugMode,         # Enable debug logging
    [switch]$ErrorsOnly,        # Monitor only error logs
    [switch]$NoAutoOpen,        # Don't auto-open browser
    [int]$BackendWait = 50      # Seconds to wait for backend (default 50)
)

Write-Host "🚀 SocioRAG Enhanced Startup" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""

# Check directory
if (-not (Test-Path "backend\app\main.py")) {
    Write-Host "❌ Error: Run this from the SocioRAG root directory" -ForegroundColor Red
    exit 1
}

# Create logs directory if it doesn't exist
$logsDir = "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "📁 Created logs directory" -ForegroundColor Green
}

# Prepare backend command
$backendCmd = "python -m backend.app.main"
if ($DebugMode) {
    $backendCmd += " --log-level debug"
    Write-Host "🔧 Debug mode enabled" -ForegroundColor Yellow
}

# Start backend
Write-Host "🔧 Starting Backend (this takes ~$BackendWait seconds)..." -ForegroundColor Cyan

$windowStyle = if ($ShowBackend) { "Normal" } else { "Hidden" }
$backendProcess = Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; $backendCmd" -WindowStyle $windowStyle -PassThru

Write-Host "🔄 Backend process started (PID: $($backendProcess.Id))" -ForegroundColor Green

# Start log monitoring if requested
$monitorJob = $null
if ($Monitor) {
    Write-Host "🔍 Starting log monitor..." -ForegroundColor Cyan
    
    $monitorScript = ".\monitor_logs.ps1"
    $monitorArgs = @("-Tail")
    
    if ($ErrorsOnly) {
        $monitorArgs += "-Errors"
    }
    
    $monitorJob = Start-Job -ScriptBlock {
        param($script, $args, $workingDir)
        Set-Location $workingDir
        & $script @args
    } -ArgumentList $monitorScript, $monitorArgs, $PWD
    
    Write-Host "📊 Log monitor started (Job ID: $($monitorJob.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# Wait for backend with improved feedback
Write-Host "⏳ Waiting for backend to initialize (up to $BackendWait seconds)..." -ForegroundColor Yellow

$attempts = 0
$maxAttempts = [math]::Ceiling($BackendWait / 3)
$backendReady = $false

do {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend is ready!" -ForegroundColor Green
            $backendReady = $true
            break
        }
    }
    catch {
        $attempts++
        $remainingTime = ($maxAttempts - $attempts) * 3
        
        if ($attempts -le $maxAttempts) {
            Write-Host "   Still waiting... (attempt $attempts/$maxAttempts, ~${remainingTime}s remaining)" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Backend failed to start within $BackendWait seconds" -ForegroundColor Red
            Write-Host "   Check logs for errors:" -ForegroundColor Yellow
            Write-Host "   .\monitor_logs.ps1 -Errors" -ForegroundColor White
            
            # Clean up
            if ($monitorJob) {
                Stop-Job $monitorJob -ErrorAction SilentlyContinue
                Remove-Job $monitorJob -ErrorAction SilentlyContinue
            }
            exit 1
        }
        Start-Sleep -Seconds 3
    }
} while (-not $backendReady)

# Start frontend
Write-Host ""
Write-Host "🎨 Starting Frontend..." -ForegroundColor Cyan
Set-Location "ui"

# Check if frontend dependencies are installed
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    try {
        if (Get-Command pnpm -ErrorAction SilentlyContinue) {
            pnpm install
        } elseif (Get-Command npm -ErrorAction SilentlyContinue) {
            npm install
        } else {
            Write-Host "❌ No package manager found (pnpm or npm required)" -ForegroundColor Red
            Set-Location ..
            exit 1
        }
    }
    catch {
        Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}

# Start frontend
$frontendWindowStyle = if ($Monitor) { "Minimized" } else { "Normal" }
$frontendProcess = Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; pnpm run dev" -WindowStyle $frontendWindowStyle -PassThru

Set-Location ..

# Wait for frontend
Start-Sleep -Seconds 5

# Display URLs
Write-Host ""
Write-Host "🎉 SocioRAG is Ready!" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend:  http://localhost:5173" -ForegroundColor White
Write-Host "Backend:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Quick Start:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:5173 in your browser" -ForegroundColor White
Write-Host "   2. Use Upload tab to add PDF documents" -ForegroundColor White
Write-Host "   3. Use Search tab to ask questions" -ForegroundColor White
Write-Host ""

# Monitoring info
if ($Monitor) {
    Write-Host "📊 Monitoring Information:" -ForegroundColor Cyan
    Write-Host "   • Log monitor is running in background" -ForegroundColor White
    Write-Host "   • View logs manually: .\monitor_logs.ps1" -ForegroundColor White
    Write-Host "   • Error logs only: .\monitor_logs.ps1 -Errors" -ForegroundColor White
    Write-Host "   • Debug logs: .\monitor_logs.ps1 -Debug" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "📊 Log Monitoring:" -ForegroundColor Cyan
    Write-Host "   • View real-time logs: .\monitor_logs.ps1 -Tail" -ForegroundColor White
    Write-Host "   • Error logs only: .\monitor_logs.ps1 -Errors -Tail" -ForegroundColor White
    Write-Host "   • Recent logs: .\monitor_logs.ps1" -ForegroundColor White
    Write-Host ""
}

Write-Host "🔧 Process Information:" -ForegroundColor Cyan
Write-Host "   • Backend PID: $($backendProcess.Id)" -ForegroundColor White
Write-Host "   • Frontend PID: $($frontendProcess.Id)" -ForegroundColor White
Write-Host ""

# Open browser unless disabled
if (-not $NoAutoOpen) {
    Write-Host "🌐 Opening frontend in your browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:5173"
}

Write-Host ""
Write-Host "✅ Startup complete!" -ForegroundColor Green

# If monitoring, show recent monitor output
if ($Monitor -and $monitorJob) {
    Write-Host ""
    Write-Host "📊 Recent log activity:" -ForegroundColor Cyan
    Write-Host "─────────────────────" -ForegroundColor Gray
    
    # Get some output from the monitoring job
    Start-Sleep -Seconds 2
    Receive-Job $monitorJob -Keep | Select-Object -Last 10 | ForEach-Object {
        Write-Host $_ -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "🔄 Log monitoring continues in background..." -ForegroundColor Green
    Write-Host "   Stop monitoring: Stop-Job $($monitorJob.Id); Remove-Job $($monitorJob.Id)" -ForegroundColor White
    Write-Host "   View monitor output: Receive-Job $($monitorJob.Id)" -ForegroundColor White
}
