@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   SocioRAG Application Startup
echo ========================================
echo.

:: Check if we're in the right directory
if not exist "backend\app\main.py" (
    echo ERROR: backend\app\main.py not found.
    echo Please run this script from the SocioRAG root directory.
    pause
    exit /b 1
)

echo [1/3] Starting Backend API Server...
echo.

:: Start backend in background
start /B "SocioRAG Backend" python -m backend.app.main

:: Wait for backend to be ready
echo Waiting for backend to initialize...
timeout /t 10 /nobreak >nul

:: Check if backend is responding
echo Checking backend status...
for /l %%i in (1,1,10) do (
    curl -s http://127.0.0.1:8000/docs >nul 2>&1
    if !errorlevel! equ 0 (
        echo Backend is ready!
        goto :backend_ready
    )
    echo Waiting... (attempt %%i/10)
    timeout /t 3 /nobreak >nul
)

echo WARNING: Backend may still be starting. Continuing with frontend...

:backend_ready
echo.
echo [2/3] Starting Frontend Development Server...
echo.

:: Change to UI directory and start frontend
cd ui
start /B "SocioRAG Frontend" pnpm run dev

:: Wait a moment for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Application Ready!
echo.
echo ========================================
echo   ACCESS YOUR APPLICATION
echo ========================================
echo.
echo Frontend:  http://localhost:5173
echo            (or check the frontend terminal for exact port)
echo.
echo Backend:   http://127.0.0.1:8000
echo API Docs:  http://127.0.0.1:8000/docs
echo.
echo ========================================
echo   QUICK START GUIDE
echo ========================================
echo.
echo 1. Open http://localhost:5173 in your browser
echo 2. Click the "Upload" tab
echo 3. Drag and drop PDF files to upload
echo 4. Wait for processing to complete
echo 5. Switch to "Search" tab
echo 6. Ask questions about your documents
echo.
echo Press any key to open the frontend in your default browser...
pause >nul

:: Open frontend in default browser
start http://localhost:5173

echo.
echo Application is running!
echo Close this window to stop the services.
echo.
pause
