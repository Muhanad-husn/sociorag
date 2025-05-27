# Simple SocioRAG Startup Script
# Starts backend, waits for it to be ready, then starts frontend

Write-Host "🚀 Starting SocioRAG Application..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Check directory
if (-not (Test-Path "backend\app\main.py")) {
    Write-Host "❌ Error: Run this from the SocioRAG root directory" -ForegroundColor Red
    exit 1
}

# Start backend
Write-Host "🔧 Starting Backend (this takes ~15 seconds)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; python -m backend.app.main" -WindowStyle Hidden

# Wait for backend
Write-Host "⏳ Waiting for backend to load dependencies..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Test backend
$attempts = 0
do {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        $attempts++
        if ($attempts -gt 10) {
            Write-Host "❌ Backend failed to start" -ForegroundColor Red
            exit 1
        }
        Write-Host "   Still waiting... (attempt $attempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
} while ($true)

# Start frontend
Write-Host ""
Write-Host "🎨 Starting Frontend..." -ForegroundColor Cyan
Set-Location "ui"
Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; pnpm run dev" -WindowStyle Normal

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

# Open browser
Write-Host "🌐 Opening frontend in your browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "✅ Startup complete! Check your browser." -ForegroundColor Green
