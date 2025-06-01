# Clean Cache Script for SocioRAG
# This script cleans all cache files and directories in the repository

Write-Host "Starting cache cleanup..." -ForegroundColor Cyan

# Count files and directories before cleanup
$initialCount = (Get-ChildItem -Path . -Recurse | Measure-Object).Count
Write-Host "Initial file/directory count: $initialCount" -ForegroundColor Yellow

# Function to remove items safely
function Remove-SafeItem {
    param (
        [string]$Pattern,
        [string]$Description,
        [switch]$IsDirectory = $false
    )
    
    Write-Host "Cleaning $Description..." -NoNewline
    
    try {
        if ($IsDirectory) {
            $items = Get-ChildItem -Path . -Directory -Recurse -Force -ErrorAction SilentlyContinue | 
                Where-Object { $_.FullName -like $Pattern }
        } else {
            $items = Get-ChildItem -Path . -File -Recurse -Force -ErrorAction SilentlyContinue | 
                Where-Object { $_.FullName -like $Pattern }
        }
        
        $count = ($items | Measure-Object).Count
        
        if ($count -gt 0) {
            $items | ForEach-Object {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
            Write-Host " Removed $count items" -ForegroundColor Green
        } else {
            Write-Host " None found" -ForegroundColor Gray
        }
    } catch {
        Write-Host " Error: $_" -ForegroundColor Red
    }
}

# Clean Python cache files and directories
Remove-SafeItem -Pattern "*\__pycache__*" -Description "Python __pycache__ directories" -IsDirectory
Remove-SafeItem -Pattern "*\.pytest_cache*" -Description "pytest cache directories" -IsDirectory
Remove-SafeItem -Pattern "*\*.pyc" -Description "Python compiled files"
Remove-SafeItem -Pattern "*\*.pyo" -Description "Python optimized files"
Remove-SafeItem -Pattern "*\*.pyd" -Description "Python extension modules"
Remove-SafeItem -Pattern "*\LOCAL_APPDATA_FONTCONFIG_CACHE*" -Description "Fontconfig cache" -IsDirectory

# Clean distribution and build files
Remove-SafeItem -Pattern "*\dist*" -Description "Distribution directories" -IsDirectory
Remove-SafeItem -Pattern "*\build*" -Description "Build directories" -IsDirectory
Remove-SafeItem -Pattern "*\*.egg-info*" -Description "Python egg info" -IsDirectory

# Clean IDE cache files
Remove-SafeItem -Pattern "*\.idea*" -Description "IDE files (IntelliJ)" -IsDirectory
Remove-SafeItem -Pattern "*\.vscode*" -Description "IDE files (VSCode)" -IsDirectory

# Clean test cache
Remove-SafeItem -Pattern "*\.coverage" -Description "Coverage files"
Remove-SafeItem -Pattern "*\htmlcov*" -Description "HTML coverage reports" -IsDirectory
Remove-SafeItem -Pattern "*\.cache*" -Description "Generic cache directories" -IsDirectory

# Clean temporary and backup files
Remove-SafeItem -Pattern "*\*.bak" -Description "Backup files"
Remove-SafeItem -Pattern "*\*.backup" -Description "Backup files"
Remove-SafeItem -Pattern "*\*.bak2" -Description "Backup files"

# Count files and directories after cleanup
$finalCount = (Get-ChildItem -Path . -Recurse | Measure-Object).Count
$removedCount = $initialCount - $finalCount

Write-Host "`nCleaning complete!" -ForegroundColor Cyan
Write-Host "Removed approximately $removedCount files/directories" -ForegroundColor Green
Write-Host "Current file/directory count: $finalCount" -ForegroundColor Yellow
