# SocioRAG Process Cleanup Script
# This script finds and terminates all processes associated with the SocioRAG application

Write-Host "SocioRAG Process Cleanup" -ForegroundColor Cyan
Write-Host "------------------------" -ForegroundColor Cyan

# Define the ports used by the application
$ports = @(8000, 5173)  # Backend and Frontend ports

# Find and kill processes by port
foreach ($port in $ports) {
    Write-Host "Looking for processes using port $port..." -ForegroundColor Yellow
    
    # Find process using this port
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | 
               Select-Object -ExpandProperty OwningProcess -Unique
    
    if ($process) {
        foreach ($pid in $process) {
            $procInfo = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($procInfo) {
                Write-Host "Found process: $($procInfo.Name) (PID: $pid) using port $port" -ForegroundColor Green
                
                try {
                    Stop-Process -Id $pid -Force
                    Write-Host "Successfully terminated process $($procInfo.Name) (PID: $pid)" -ForegroundColor Green
                } catch {
                    Write-Host "Failed to terminate process $($procInfo.Name) (PID: $pid): $_" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "No processes found using port $port" -ForegroundColor Gray
    }
}

# Find and kill specific application processes by name patterns
$processPatterns = @(
    "python*",      # Python processes (likely running backend)
    "node",         # Node.js processes (likely running frontend)
    "npm",          # NPM processes
    "uvicorn*",     # Uvicorn server (common for FastAPI backends)
    "vite"          # Vite dev server (common for modern frontend)
)

Write-Host "`nLooking for processes by name pattern..." -ForegroundColor Yellow
foreach ($pattern in $processPatterns) {
    $processes = Get-Process -Name $pattern -ErrorAction SilentlyContinue
    
    foreach ($proc in $processes) {
        # Try to determine if this is related to our app by checking command line arguments
        # This helps avoid killing unrelated Python/Node processes
        $isAppProcess = $false
        
        try {
            $cmdLine = (Get-WmiObject -Class Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            
            # Check if command line contains any of these app-related paths
            if ($cmdLine -match "sociorag|backend\\app|uvicorn|vite.*5173|npm.*run.*dev") {
                $isAppProcess = $true
            }
        } catch {
            # If we can't check the command line, we'll be cautious and not kill it
            $isAppProcess = $false
        }
        
        if ($isAppProcess) {
            Write-Host "Found app process: $($proc.Name) (PID: $($proc.Id))" -ForegroundColor Green
            
            try {
                Stop-Process -Id $proc.Id -Force
                Write-Host "Successfully terminated process $($proc.Name) (PID: $($proc.Id))" -ForegroundColor Green
            } catch {
                Write-Host "Failed to terminate process $($proc.Name) (PID: $($proc.Id)): $_" -ForegroundColor Red
            }
        } else {
            Write-Host "Skipping non-app process: $($proc.Name) (PID: $($proc.Id))" -ForegroundColor Gray
        }
    }
}

# Check for any child processes spawned by the PowerShell scripts
Write-Host "`nLooking for child processes spawned by PowerShell scripts..." -ForegroundColor Yellow
$psScripts = @(
    "unified_start.ps1",
    "app_manager.ps1",
    "monitoring_dashboard.ps1",
    "performance_monitor.ps1"
)

foreach ($script in $psScripts) {
    $processes = Get-WmiObject -Class Win32_Process -Filter "CommandLine LIKE '%$script%'"
    
    foreach ($proc in $processes) {
        try {
            Write-Host "Found script process: (PID: $($proc.ProcessId)) running $script" -ForegroundColor Green
            Stop-Process -Id $proc.ProcessId -Force
            Write-Host "Successfully terminated process (PID: $($proc.ProcessId))" -ForegroundColor Green
        } catch {
            Write-Host "Failed to terminate process (PID: $($proc.ProcessId)): $_" -ForegroundColor Red
        }
    }
}

# Clean up any PID files that might exist
if (Test-Path "logs\sociorag.pid") {
    Remove-Item "logs\sociorag.pid" -Force
    Write-Host "`nRemoved PID file" -ForegroundColor Cyan
}

Write-Host "`nCleanup complete!" -ForegroundColor Cyan
