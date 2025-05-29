# Quick Stop for SocioRAG Production
# Stops all SocioRAG processes cleanly

Write-Host "🛑 Stopping SocioRAG..." -ForegroundColor Yellow

# Stop Python backend
$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*backend*" }
if ($pythonProcesses) {
    Write-Host "📡 Stopping backend..." -ForegroundColor Cyan
    $pythonProcesses | Stop-Process -Force
    Write-Host "✅ Backend stopped" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No backend process found" -ForegroundColor Gray
}

# Stop Node frontend
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Write-Host "🎨 Stopping frontend..." -ForegroundColor Cyan
    $nodeProcesses | Stop-Process -Force
    Write-Host "✅ Frontend stopped" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No frontend process found" -ForegroundColor Gray
}

Write-Host "🎯 SocioRAG stopped successfully!" -ForegroundColor Green
