# Simple Production Start - SocioRAG
# Starts backend, frontend, opens browser, and monitors performance

Write-Host "🚀 Starting SocioRAG for Production Use" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Ensure we're working from the project root
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $ProjectRoot
Write-Host "Working from: $ProjectRoot" -ForegroundColor Gray

# 1. Start Backend
Write-Host "📡 Starting Backend..." -ForegroundColor Cyan
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python -m backend.app.main" -WindowStyle Minimized

# Wait for backend to load
Write-Host "⏳ Waiting for backend to initialize (20 seconds)..." -ForegroundColor Yellow
Write-Host "   (Backend initialization typically takes 12-15 seconds)" -ForegroundColor Gray
Start-Sleep 20

# 2. Test Backend
Write-Host "🔍 Testing backend connection..." -ForegroundColor Cyan
$maxRetries = 5
$retryCount = 0
$backendReady = $false

while ($retryCount -lt $maxRetries -and -not $backendReady) {
    try {
        $retryCount++
        Write-Host "Attempt $retryCount/$maxRetries..." -ForegroundColor Gray
        
        # Try the health endpoint first, fallback to root
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/health" -TimeoutSec 10
            Write-Host "✅ Backend health check passed!" -ForegroundColor Green
            $backendReady = $true
        }
        catch {
            # Fallback to root endpoint
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -TimeoutSec 10
            if ($response.status -eq "ok") {
                Write-Host "✅ Backend is running!" -ForegroundColor Green
                $backendReady = $true
            }
        }
    }
    catch {
        if ($retryCount -lt $maxRetries) {
            Write-Host "⏳ Backend still initializing, waiting 5 seconds..." -ForegroundColor Yellow
            Start-Sleep 5
        }
    }
}

if (-not $backendReady) {
    Write-Host "❌ Backend failed to start properly after $maxRetries attempts" -ForegroundColor Red
    Write-Host "Check the backend window for errors" -ForegroundColor Yellow
    Write-Host "Backend logs show initialization takes ~12-15 seconds..." -ForegroundColor Gray
    Read-Host "Press Enter to continue anyway or Ctrl+C to stop"
}

# 3. Check Frontend Dependencies
Write-Host "🔍 Checking frontend dependencies..." -ForegroundColor Cyan
$frontendPath = "$ProjectRoot\ui"
$nodeModulesPath = "$frontendPath\node_modules"
$vitePath = "$nodeModulesPath\vite\dist\node\cli.js"

if (-not (Test-Path $vitePath)) {
    Write-Host "⚠️  Frontend dependencies missing or corrupted" -ForegroundColor Yellow
    Write-Host "🔧 Reinstalling frontend dependencies..." -ForegroundColor Cyan
    
    Set-Location $frontendPath
    
    # Remove corrupted node_modules and package-lock
    if (Test-Path $nodeModulesPath) {
        Write-Host "   Removing corrupted node_modules..." -ForegroundColor Gray
        Remove-Item -Path $nodeModulesPath -Recurse -Force
    }
    if (Test-Path "package-lock.json") {
        Remove-Item -Path "package-lock.json" -Force
    }
    
    # Reinstall dependencies
    Write-Host "   Installing dependencies..." -ForegroundColor Gray
    $installResult = & npm install 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
        Write-Host "Error: $installResult" -ForegroundColor Red
        Set-Location $ProjectRoot
        Read-Host "Press Enter to continue anyway or Ctrl+C to stop"
    }
    
    Set-Location $ProjectRoot
}

# 4. Start Frontend
Write-Host "🎨 Starting Frontend..." -ForegroundColor Cyan
Set-Location "$ProjectRoot\ui"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Minimized
Set-Location $ProjectRoot

# Wait for frontend
Write-Host "⏳ Waiting for frontend to start (10 seconds)..." -ForegroundColor Yellow
Start-Sleep 10

# 5. Open Browser
Write-Host "🌐 Opening browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

# 6. Start Monitoring
Write-Host "📊 Starting Performance Monitor..." -ForegroundColor Cyan
Write-Host ""
Write-Host "=== SocioRAG is Running ===" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "Backend API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "📊 Performance monitoring starting..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring (apps will keep running)" -ForegroundColor Yellow
Write-Host ""

# Simple monitoring loop
$startTime = Get-Date
while ($true) {
    try {
        # Check API health
        $apiStart = Get-Date
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/admin/health" -TimeoutSec 3
        $apiTime = [math]::Round(((Get-Date) - $apiStart).TotalMilliseconds, 1)
        
        # Get system info
        $cpu = [math]::Round((Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples.CookedValue, 1)
        $memoryGB = [math]::Round((Get-Process python | Where-Object {$_.ProcessName -eq "python"} | Measure-Object WorkingSet -Sum).Sum / 1GB, 2)
        
        # Calculate uptime
        $uptime = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
        
        # Status display
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "✅ API: ${apiTime}ms " -NoNewline -ForegroundColor Green
        Write-Host "| CPU: $cpu% " -NoNewline -ForegroundColor $(if($cpu -gt 80){"Red"}elseif($cpu -gt 60){"Yellow"}else{"Green"})
        Write-Host "| Memory: ${memoryGB}GB " -NoNewline -ForegroundColor $(if($memoryGB -gt 3){"Red"}elseif($memoryGB -gt 2){"Yellow"}else{"Green"})
        Write-Host "| Uptime: ${uptime}m" -ForegroundColor Cyan
        
    }
    catch {
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] ❌ API not responding" -ForegroundColor Red
    }
    
    Start-Sleep 30
}
