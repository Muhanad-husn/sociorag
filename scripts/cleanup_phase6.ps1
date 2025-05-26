# Script to clean up and organize Phase 6 files
# Created during Phase 6 housekeeping

# Set absolute paths
$rootDir = "D:\sociorag"
$backendDir = "$rootDir\backend"
$docsDir = "$rootDir\docs"
$scriptsDir = "$rootDir\scripts"

# Step 1: Rename files to match imports in main.py
Write-Host "Renaming files to match imports in main.py..."

# Check if history.py exists and history_new.py doesn't
if ((Test-Path "$backendDir\app\api\history.py") -and -not (Test-Path "$backendDir\app\api\history_new.py")) {
    Move-Item -Path "$backendDir\app\api\history.py" -Destination "$backendDir\app\api\history_new.py"
    Write-Host "Renamed history.py to history_new.py"
}

# Check if websocket.py exists and websocket_new.py doesn't
if ((Test-Path "$backendDir\app\api\websocket.py") -and -not (Test-Path "$backendDir\app\api\websocket_new.py")) {
    Move-Item -Path "$backendDir\app\api\websocket.py" -Destination "$backendDir\app\api\websocket_new.py"
    Write-Host "Renamed websocket.py to websocket_new.py"
}

# Step 2: Create a backup of files to be removed
$backupDir = "$rootDir\phase6_backup_cleanup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
Write-Host "Created backup directory: $backupDir"

$filesToBackup = @(
    "$backendDir\app\api\export_backup.py",
    "$backendDir\app\api\search_backup.py",
    "$backendDir\app\api\search_backup2.py",
    "$backendDir\app\api\search_backup3.py",
    "$backendDir\app\api\search_new.py",
    "$backendDir\app\api\websocket_backup.py",
    "$scriptsDir\test_api_endpoints.py"
)

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        $destPath = Join-Path -Path $backupDir -ChildPath (Split-Path -Path $file -Leaf)
        Copy-Item -Path $file -Destination $destPath
        Write-Host "Backed up: $file"
    }
}

# Step 3: Remove backup files after backing them up
Write-Host "Removing backup files..."
foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        Remove-Item -Path $file
        Write-Host "Removed: $file"
    }
}

# Step 4: Add files to git
Write-Host "Adding files to git..."

# Files to add
$filesToAdd = @(
    "$rootDir\PHASE6_HOUSEKEEPING_REPORT.md",
    "$docsDir\api_endpoints_reference.md",
    "$docsDir\phase6_housekeeping_summary.md",
    "$docsDir\phase6_implementation_summary.md",
    "$docsDir\phase6_progress_status_report.md",
    "$docsDir\phase7_implementation_plan.md",
    "$backendDir\app\api\admin.py",
    "$backendDir\app\api\documents.py",
    "$backendDir\app\api\export.py",
    "$backendDir\app\api\history_new.py",
    "$backendDir\app\api\search.py",
    "$backendDir\app\api\websocket_new.py",
    "$scriptsDir\backup_phase6.ps1",
    "$scriptsDir\prepare_phase7.ps1",
    "$scriptsDir\test_phase6_api.py",
    "$scriptsDir\cleanup_phase6.ps1",
    "$rootDir\README.md",
    "$backendDir\app\api\qa.py",
    "$rootDir\instructions\phase6_deep_dive_plan.md",
    "$rootDir\requirements.txt",
    "$rootDir\phase6_unstaged_files_management.md"
)

# Add each file to git
foreach ($file in $filesToAdd) {
    if (Test-Path $file) {
        git add $file
        Write-Host "Added to git: $file"
    } else {
        Write-Host "Warning: File not found - $file"
    }
}

Write-Host ""
Write-Host "Phase 6 cleanup complete!"
Write-Host "Backup of removed files: $backupDir"
Write-Host "Check git status to verify changes"
