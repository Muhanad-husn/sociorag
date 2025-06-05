# SocioRAG Setup Script
# Run this script after cloning the repository to set up the development environment

param(
    [switch]$SkipPython,
    [switch]$SkipFrontend,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

function Write-SetupLog {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    Write-Host "[$timestamp][$Level] $Message" -ForegroundColor $color
}

function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
}

Write-SetupLog "🚀 Setting up SocioRAG development environment..." "INFO"

# Ensure we're in the project root
if (-not (Test-Path "backend\app\main.py")) {
    Write-SetupLog "Error: Please run this script from the SocioRAG root directory" "ERROR"
    exit 1
}

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-SetupLog "Created logs directory" "SUCCESS"
}

# Check Python installation
if (-not $SkipPython) {
    Write-SetupLog "Checking Python installation..." "INFO"
    
    if (-not (Test-Command "python")) {
        Write-SetupLog "Python not found. Please install Python 3.8+ and add it to PATH" "ERROR"
        exit 1
    }
    
    $pythonVersion = python --version
    Write-SetupLog "Found Python: $pythonVersion" "SUCCESS"
    
    # Install Python dependencies
    Write-SetupLog "Installing Python dependencies..." "INFO"
    try {
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
        Write-SetupLog "Python dependencies installed successfully!" "SUCCESS"
    }
    catch {
        Write-SetupLog "Failed to install Python dependencies: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Check Node.js and setup frontend
if (-not $SkipFrontend) {
    Write-SetupLog "Checking Node.js installation..." "INFO"
    
    if (-not (Test-Command "node")) {
        Write-SetupLog "Node.js not found. Please install Node.js 18+ and add it to PATH" "ERROR"
        exit 1
    }
    
    $nodeVersion = node --version
    Write-SetupLog "Found Node.js: $nodeVersion" "SUCCESS"
    
    # Install frontend dependencies
    if (Test-Path "ui") {
        Write-SetupLog "Installing frontend dependencies..." "INFO"
        
        try {
            Push-Location "ui"
            
            # Determine package manager
            $packageManager = "npm"
            if (Test-Path "pnpm-lock.yaml") {
                if (Test-Command "pnpm") {
                    $packageManager = "pnpm"
                } else {
                    Write-SetupLog "pnpm-lock.yaml found but pnpm not installed. Using npm instead." "WARNING"
                }
            } elseif (Test-Path "yarn.lock") {
                if (Test-Command "yarn") {
                    $packageManager = "yarn"
                } else {
                    Write-SetupLog "yarn.lock found but yarn not installed. Using npm instead." "WARNING"
                }
            }
            
            Write-SetupLog "Installing dependencies using $packageManager..." "INFO"
            
            & $packageManager install
            
            if ($LASTEXITCODE -eq 0) {
                Write-SetupLog "Frontend dependencies installed successfully!" "SUCCESS"
            } else {
                Write-SetupLog "Failed to install frontend dependencies" "ERROR"
                exit 1
            }
        }
        catch {
            Write-SetupLog "Error installing frontend dependencies: $($_.Exception.Message)" "ERROR"
            exit 1
        }
        finally {
            Pop-Location
        }
    }
}

# Initialize database if needed
Write-SetupLog "Checking database setup..." "INFO"
if (-not (Test-Path "data\graph.db")) {
    Write-SetupLog "Initializing database..." "INFO"
    try {
        python scripts\init_database_schema.py
        Write-SetupLog "Database initialized successfully!" "SUCCESS"
    }
    catch {
        Write-SetupLog "Failed to initialize database: $($_.Exception.Message)" "WARNING"
    }
}

Write-SetupLog "✅ Setup completed successfully!" "SUCCESS"
Write-SetupLog "" "INFO"
Write-SetupLog "Next steps:" "INFO"
Write-SetupLog "  1. Run: .\start_production.ps1" "INFO"
Write-SetupLog "  2. Open: http://localhost:5173" "INFO"
Write-SetupLog "" "INFO"
