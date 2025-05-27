# SocioRAG Application Startup Script
# This script starts the backend API server, waits for it to be ready,
# then starts the frontend development server and displays access links.

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [int]$BackendPort = 8000,
    [int]$TimeoutSeconds = 60
)

# Color functions for better output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }

# Function to check if a port is available
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("127.0.0.1", $Port)
        $connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

# Function to wait for backend to be ready
function Wait-ForBackend {
    param([int]$Port, [int]$TimeoutSeconds)
    
    Write-Info "⏳ Waiting for backend to be ready on port $Port..."
    Write-Info "   (This may take 10-15 seconds for heavy dependencies to load...)"
    $startTime = Get-Date
    
    do {
        Start-Sleep -Seconds 3
        $elapsed = (Get-Date) - $startTime
        
        if ($elapsed.TotalSeconds -gt $TimeoutSeconds) {
            Write-Error "❌ Timeout waiting for backend to start after $TimeoutSeconds seconds"
            Write-Info "💡 Backend startup involves loading spaCy, graph modules, and WeasyPrint"
            Write-Info "   Try increasing timeout with: .\start_app.ps1 -TimeoutSeconds 90"
            return $false
        }
        
        try {
            # First check if the port is responding at all
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ReceiveTimeout = 3000
            $tcpClient.SendTimeout = 3000
            $connection = $tcpClient.BeginConnect("127.0.0.1", $Port, $null, $null)
            $success = $connection.AsyncWaitHandle.WaitOne(3000, $false)
            $tcpClient.Close()
            
            if ($success) {
                # If port is responding, try the docs endpoint
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/docs" -TimeoutSec 5 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Success "✅ Backend is ready!"
                    return $true
                }
            }
        }
        catch {
            # Expected during startup
        }
        
        $elapsedSeconds = [math]::Round($elapsed.TotalSeconds, 0)
        Write-Host "   Waiting... ($elapsedSeconds/$TimeoutSeconds seconds)" -ForegroundColor Yellow
        
    } while ($true)
}

# Main script
Write-Info "🚀 Starting SocioRAG Application..."
Write-Info "==============================================="

# Check if we're in the right directory
if (-not (Test-Path "backend\app\main.py")) {
    Write-Error "❌ Error: backend\app\main.py not found. Please run this script from the SocioRAG root directory."
    exit 1
}

# Start Backend
if (-not $SkipBackend) {
    Write-Info "🔧 Starting Backend API Server..."
    
    # Check if backend port is already in use
    if (Test-Port -Port $BackendPort) {
        Write-Warning "⚠️  Port $BackendPort is already in use. Backend might already be running."
        Write-Info "📍 Backend should be available at: http://127.0.0.1:$BackendPort"
        Write-Info "📚 API documentation at: http://127.0.0.1:$BackendPort/docs"
    }
    else {
        # Start backend in background
        $backendJob = Start-Job -ScriptBlock {
            param($WorkingDir)
            Set-Location $WorkingDir
            python -m backend.app.main
        } -ArgumentList (Get-Location).Path
        
        Write-Info "🔄 Backend job started (Job ID: $($backendJob.Id))"
        
        # Wait for backend to be ready
        if (-not (Wait-ForBackend -Port $BackendPort -TimeoutSeconds $TimeoutSeconds)) {
            Write-Error "❌ Failed to start backend. Stopping script."
            Stop-Job $backendJob -ErrorAction SilentlyContinue
            Remove-Job $backendJob -ErrorAction SilentlyContinue
            exit 1
        }
        
        Write-Success "✅ Backend is running!"
        Write-Info "📍 Backend API: http://127.0.0.1:$BackendPort"
        Write-Info "📚 API Docs: http://127.0.0.1:$BackendPort/docs"
    }
}

# Start Frontend
if (-not $SkipFrontend) {
    Write-Info ""
    Write-Info "🎨 Starting Frontend Development Server..."
    
    # Change to UI directory and start frontend
    Push-Location "ui"
    
    try {
        Write-Info "🔄 Running 'pnpm run dev'..."
        
        # Start frontend and capture output to find the port
        $frontendProcess = Start-Process -FilePath "pnpm" -ArgumentList "run", "dev" -PassThru -NoNewWindow
        
        # Give it a moment to start
        Start-Sleep -Seconds 3
        
        # Try to detect the frontend port (default attempts)
        $frontendPorts = @(5173, 5174, 5175, 5176, 5177)
        $frontendUrl = $null
        
        foreach ($port in $frontendPorts) {
            if (Test-Port -Port $port) {
                $frontendUrl = "http://localhost:$port"
                break
            }
        }
        
        if ($frontendUrl) {
            Write-Success "✅ Frontend is running!"
            Write-Info "🌐 Frontend URL: $frontendUrl"
        }
        else {
            Write-Warning "⚠️  Frontend may be starting... Check the terminal output for the exact URL."
            Write-Info "🌐 Frontend should be available at: http://localhost:5173 (or next available port)"
        }
    }
    catch {
        Write-Error "❌ Failed to start frontend: $($_.Exception.Message)"
    }
    finally {
        Pop-Location
    }
}

# Final summary
Write-Info ""
Write-Success "🎉 SocioRAG Application Startup Complete!"
Write-Info "==============================================="
Write-Info "📱 Access your application:"
Write-Info "   Frontend:  http://localhost:5173 (or check terminal for exact port)"
Write-Info "   Backend:   http://127.0.0.1:$BackendPort"
Write-Info "   API Docs:  http://127.0.0.1:$BackendPort/docs"
Write-Info ""
Write-Info "💡 Quick Start:"
Write-Info "   1. Open the frontend URL in your browser"
Write-Info "   2. Go to the 'Upload' tab and upload PDF documents"
Write-Info "   3. Wait for processing to complete"
Write-Info "   4. Switch to 'Search' tab and ask questions"
Write-Info ""
Write-Warning "📝 Note: Keep this PowerShell window open to maintain the backend service."
Write-Info "   Press Ctrl+C to stop the backend when you're done."

# Keep the script running to maintain backend (if we started it)
if (-not $SkipBackend -and $backendJob) {
    Write-Info ""
    Write-Info "⏳ Backend is running in the background..."
    Write-Info "   Press Ctrl+C to stop all services and exit."
    
    try {
        # Wait for user to interrupt or job to complete
        while ($backendJob.State -eq "Running") {
            Start-Sleep -Seconds 5
            
            # Check if job is still running
            if ($backendJob.State -ne "Running") {
                break
            }
        }
    }
    catch {
        Write-Info "`n🛑 Stopping services..."
    }
    finally {
        # Cleanup
        if ($backendJob) {
            Stop-Job $backendJob -ErrorAction SilentlyContinue
            Remove-Job $backendJob -ErrorAction SilentlyContinue
            Write-Info "✅ Backend service stopped."
        }
    }
}
