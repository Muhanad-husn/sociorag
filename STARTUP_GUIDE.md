# SocioRAG Application Startup Scripts

This directory contains convenient startup scripts to launch the SocioRAG application with both backend and frontend services.

## Quick Start

### Option 1: Quick Start Script (Easiest)
```powershell
.\quick_start.ps1
```

### Option 2: PowerShell Script (Advanced)
```powershell
.\start_app.ps1
```

### Option 3: Batch File
```cmd
start_app.bat
```

## Script Features

### PowerShell Script (`start_app.ps1`)
- ✅ Starts backend API server
- ✅ Waits for backend to be fully ready
- ✅ Starts frontend development server
- ✅ Displays access URLs
- ✅ Provides colored output and status updates
- ✅ Handles port conflicts gracefully
- ✅ Keeps backend running until interrupted

**Advanced Options:**
```powershell
# Skip backend startup (if already running)
.\start_app.ps1 -SkipBackend

# Skip frontend startup
.\start_app.ps1 -SkipFrontend

# Use custom backend port
.\start_app.ps1 -BackendPort 8080

# Custom timeout for backend startup
.\start_app.ps1 -TimeoutSeconds 60
```

### Batch File (`start_app.bat`)
- ✅ Simple startup sequence
- ✅ Automatic browser opening
- ✅ Basic error handling
- ✅ User-friendly output

## What the Scripts Do

1. **Backend Startup**: Launches the FastAPI server on `http://127.0.0.1:8000`
   - Loads spaCy model (~1 second)
   - Initializes graph retrieval modules (~6 seconds)
   - Loads WeasyPrint for PDF generation
   - **Total startup time: ~10-15 seconds**
2. **Health Check**: Waits for the backend to be fully responsive
3. **Frontend Startup**: Launches the Vite dev server (usually on `http://localhost:5173`)
4. **URL Display**: Shows all access URLs for easy copy-paste

## Access URLs

After successful startup, you'll have access to:

- **Frontend Application**: `http://localhost:5173` (main application interface)
- **Backend API**: `http://127.0.0.1:8000` (API endpoints)
- **API Documentation**: `http://127.0.0.1:8000/docs` (interactive Swagger UI)

## Troubleshooting

### Port Conflicts
If ports are already in use:
- Backend: The script will detect if port 8000 is occupied
- Frontend: Vite automatically tries ports 5173, 5174, 5175, etc.

### Backend Won't Start
```powershell
# Check if Python environment is activated
python --version

# Verify dependencies are installed
pip list | findstr fastapi

# Try manual startup for debugging
python -m backend.app.main
```

### Frontend Won't Start
```powershell
# Ensure you're in the ui directory
cd ui

# Check if pnpm is installed
pnpm --version

# Install dependencies if needed
pnpm install

# Try manual startup
pnpm run dev
```

### PowerShell Execution Policy
If you get execution policy errors:
```powershell
# Check current policy
Get-ExecutionPolicy

# Set policy for current user (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Manual Startup (Alternative)

If the scripts don't work, you can start services manually:

### Terminal 1 (Backend)
```powershell
cd d:\sociorag
python -m backend.app.main
```

### Terminal 2 (Frontend)
```powershell
cd d:\sociorag\ui
pnpm run dev
```

## Stopping the Application

- **PowerShell Script**: Press `Ctrl+C` in the terminal where the script is running
- **Batch Script**: Close the command window
- **Manual**: Press `Ctrl+C` in each terminal

## Environment Requirements

- Python 3.12+ with all dependencies installed
- Node.js and pnpm for frontend
- All SocioRAG dependencies as per README.md

## Quick Start After Launch

1. Open the frontend URL in your browser
2. Navigate to the "Upload" tab
3. Upload PDF documents (max 50MB each)
4. Wait for processing to complete (progress bar will show status)
5. Go to "Search" tab
6. Ask questions about your uploaded documents
7. Explore History, Saved, and Settings pages

The application will remember your uploads and settings between sessions.
