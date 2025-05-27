# Additional SocioRAG Housekeeping Script
# Cleans up remaining superseded files after Phase 7 completion
# Date: May 27, 2025

param(
    [switch]$DryRun = $false  # Use -DryRun to see what would be cleaned without actually doing it
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "d:\sociorag\cleanup_backups\additional_cleanup_$timestamp"
$rootDir = "d:\sociorag"

Write-Host "=== SocioRAG Additional Housekeeping Script ===" -ForegroundColor Cyan
Write-Host "Timestamp: $timestamp" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "*** DRY RUN MODE - No files will be actually removed ***" -ForegroundColor Yellow
}
Write-Host ""

# Create backup directory structure
if (-not $DryRun) {
    New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
    New-Item -Path "$backupDir\old_backups" -ItemType Directory -Force | Out-Null
    New-Item -Path "$backupDir\superseded_files" -ItemType Directory -Force | Out-Null
    New-Item -Path "$backupDir\cache_content" -ItemType Directory -Force | Out-Null
}

# Files/directories identified for cleanup
$itemsToCleanup = @{
    "Old Backup Directories" = @(
        "phase4_backup_20250526_045633",
        "phase6_backup_cleanup_20250526_092007"
    )
    "Superseded Configuration Files" = @(
        "environment.yml"  # Conda environment file - superseded by requirements.txt
    )
    "Development Utilities" = @(
        "fix_imports.py"  # Import fixing utility - completed task
    )
    "Cache Directories" = @(
        "LOCAL_APPDATA_FONTCONFIG_CACHE",
        ".benchmarks"
    )
}

$totalSize = 0
$fileCount = 0

Write-Host "📊 Analyzing items for cleanup..." -ForegroundColor Green

foreach ($category in $itemsToCleanup.Keys) {
    Write-Host "`n🔍 Category: $category" -ForegroundColor Yellow
    
    foreach ($item in $itemsToCleanup[$category]) {
        $fullPath = Join-Path $rootDir $item
        
        if (Test-Path $fullPath) {
            # Calculate size
            if (Test-Path $fullPath -PathType Container) {
                $size = (Get-ChildItem $fullPath -Recurse -Force | Measure-Object -Property Length -Sum).Sum
                $fileCountInDir = (Get-ChildItem $fullPath -Recurse -Force).Count
                Write-Host "  📁 $item - Directory ($fileCountInDir files, $([math]::Round($size/1MB, 2)) MB)" -ForegroundColor White
                $fileCount += $fileCountInDir
            } else {
                $size = (Get-Item $fullPath).Length
                Write-Host "  📄 $item - File ($([math]::Round($size/1KB, 2)) KB)" -ForegroundColor White
                $fileCount += 1
            }
            $totalSize += $size
        } else {
            Write-Host "  ❌ $item - Not found (already cleaned)" -ForegroundColor Gray
        }
    }
}

Write-Host "`n📈 Cleanup Summary:" -ForegroundColor Cyan
Write-Host "  Total items to process: $fileCount files/directories"
Write-Host "  Total size to clean: $([math]::Round($totalSize/1MB, 2)) MB"
Write-Host "  Backup location: $backupDir"

if ($DryRun) {
    Write-Host "`n🔍 DRY RUN COMPLETE - No changes made" -ForegroundColor Yellow
    Write-Host "Run without -DryRun flag to perform actual cleanup"
    return
}

# Confirm cleanup
Write-Host "`n⚠️  Do you want to proceed with cleanup? (y/N): " -ForegroundColor Red -NoNewline
$confirm = Read-Host
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Cleanup cancelled." -ForegroundColor Yellow
    return
}

Write-Host "`n🚀 Starting cleanup process..." -ForegroundColor Green

# Backup and remove old backup directories
foreach ($backupDirName in $itemsToCleanup["Old Backup Directories"]) {
    $sourcePath = Join-Path $rootDir $backupDirName
    if (Test-Path $sourcePath) {
        Write-Host "📦 Archiving old backup: $backupDirName"
        $targetPath = Join-Path "$backupDir\old_backups" $backupDirName
        Copy-Item -Path $sourcePath -Destination $targetPath -Recurse -Force
        Remove-Item -Path $sourcePath -Recurse -Force
        Write-Host "  ✅ Moved to archive"
    }
}

# Backup and remove superseded files
foreach ($fileName in $itemsToCleanup["Superseded Configuration Files"]) {
    $sourcePath = Join-Path $rootDir $fileName
    if (Test-Path $sourcePath) {
        Write-Host "📄 Archiving superseded file: $fileName"
        $targetPath = Join-Path "$backupDir\superseded_files" $fileName
        Copy-Item -Path $sourcePath -Destination $targetPath
        Remove-Item -Path $sourcePath -Force
        Write-Host "  ✅ Archived and removed"
    }
}

# Backup and remove development utilities
foreach ($fileName in $itemsToCleanup["Development Utilities"]) {
    $sourcePath = Join-Path $rootDir $fileName
    if (Test-Path $sourcePath) {
        Write-Host "🔧 Archiving development utility: $fileName"
        $targetPath = Join-Path "$backupDir\superseded_files" $fileName
        Copy-Item -Path $sourcePath -Destination $targetPath
        Remove-Item -Path $sourcePath -Force
        Write-Host "  ✅ Archived and removed"
    }
}

# Clean cache directories (backup first)
foreach ($cacheDirName in $itemsToCleanup["Cache Directories"]) {
    $sourcePath = Join-Path $rootDir $cacheDirName
    if (Test-Path $sourcePath) {
        Write-Host "🗄️  Cleaning cache directory: $cacheDirName"
        $targetPath = Join-Path "$backupDir\cache_content" $cacheDirName
        Copy-Item -Path $sourcePath -Destination $targetPath -Recurse -Force
        Remove-Item -Path $sourcePath -Recurse -Force
        Write-Host "  ✅ Cache cleaned (backup preserved)"
    }
}

# Create cleanup report
$reportContent = @"
# Additional SocioRAG Cleanup Report
Generated: $(Get-Date)
Backup Location: $backupDir

## Cleanup Summary
- Old Backup Directories: $($itemsToCleanup["Old Backup Directories"].Count) directories
- Superseded Files: $($itemsToCleanup["Superseded Configuration Files"].Count + $itemsToCleanup["Development Utilities"].Count) files
- Cache Directories: $($itemsToCleanup["Cache Directories"].Count) directories
- Total Size Cleaned: $([math]::Round($totalSize/1MB, 2)) MB

## Items Processed
### Old Backup Directories
$($itemsToCleanup["Old Backup Directories"] | ForEach-Object { "- $_" } | Out-String)

### Superseded Files
$($itemsToCleanup["Superseded Configuration Files"] + $itemsToCleanup["Development Utilities"] | ForEach-Object { "- $_" } | Out-String)

### Cache Directories
$($itemsToCleanup["Cache Directories"] | ForEach-Object { "- $_" } | Out-String)

## Restoration
All cleaned items have been backed up to: $backupDir
To restore any item, copy it back to the root directory from the appropriate subdirectory.

## Next Steps
1. Verify system functionality with: python final_e2e_test_working.py
2. If all tests pass, the cleanup was successful
3. Archive this backup after confirming system stability
"@

$reportContent | Out-File -FilePath "$backupDir\cleanup_report.md" -Encoding UTF8

Write-Host "`n✅ Additional cleanup completed successfully!" -ForegroundColor Green
Write-Host "📊 Results:" -ForegroundColor Cyan
Write-Host "  - Items processed: $fileCount files/directories"
Write-Host "  - Space recovered: $([math]::Round($totalSize/1MB, 2)) MB"
Write-Host "  - Backup created: $backupDir"
Write-Host ""
Write-Host "🔍 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test system: python final_e2e_test_working.py"
Write-Host "  2. If tests pass, cleanup was successful"
Write-Host "  3. Archive backup after validation"

Write-Host ""
Write-Host "🎉 Workspace is now optimally organized for production!" -ForegroundColor Green
