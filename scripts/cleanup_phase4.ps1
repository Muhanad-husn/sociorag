# Cleanup script for SocioGraph Phase 4
# Created: May 26, 2025

# Create a single consolidated backup directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "d:\sociorag\phase4_backup_$timestamp"
New-Item -Path $backupDir -ItemType Directory -Force

# Function to copy files to backup with structure preservation
function Backup-Files {
    param (
        [string]$sourcePath,
        [string]$destinationPath
    )
    
    $sourceParent = Split-Path -Parent $sourcePath
    $sourceBaseName = Split-Path -Leaf $sourcePath
    
    # Create target directory if it doesn't exist
    if (-not (Test-Path $destinationPath)) {
        New-Item -Path $destinationPath -ItemType Directory -Force | Out-Null
    }
    
    # Handle directories
    if (Test-Path $sourcePath -PathType Container) {
        $targetDir = Join-Path $destinationPath $sourceBaseName
        if (-not (Test-Path $targetDir)) {
            New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
        }
        
        # Copy all items in the directory
        Get-ChildItem $sourcePath | ForEach-Object {
            $childSourcePath = $_.FullName
            Backup-Files -sourcePath $childSourcePath -destinationPath $targetDir
        }
    } else {
        # Copy file
        Copy-Item -Path $sourcePath -Destination $destinationPath -Force
    }
}

# Backup test files and validation scripts
$filesToBackup = @(
    "d:\sociorag\test_phase4_optimizations.py",
    "d:\sociorag\test_phase4_final_validation.py",
    "d:\sociorag\validate_phase4_manual.py",
    "d:\sociorag\phase4_final_demo.py",
    "d:\sociorag\scripts\validate_phase4.py",
    "d:\sociorag\phase4_optimization_results.json",
    "d:\sociorag\phase4_final_validation_results.json"
)

$filesDir = Join-Path $backupDir "phase4_files"
New-Item -Path $filesDir -ItemType Directory -Force | Out-Null

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        $fileName = Split-Path $file -Leaf
        $fileDestination = Join-Path $filesDir $fileName
        Copy-Item -Path $file -Destination $fileDestination -Force
    }
}

# Copy all backup directories to the consolidated backup
$backupDirs = @(
    "d:\sociorag\backup_20250526_003245",
    "d:\sociorag\backup_cleanup_20250526_004727",
    "d:\sociorag\backup_cleanup_20250526_005129",
    "d:\sociorag\final_backup_20250526_005251"
)

$prevBackupDir = Join-Path $backupDir "previous_backups"
New-Item -Path $prevBackupDir -ItemType Directory -Force | Out-Null

foreach ($dir in $backupDirs) {
    if (Test-Path $dir) {
        $dirName = Split-Path $dir -Leaf
        $targetDir = Join-Path $prevBackupDir $dirName
        New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
        
        # Copy all items from the backup directory
        Get-ChildItem $dir | ForEach-Object {
            if (Test-Path $_.FullName -PathType Container) {
                # For directories, copy recursively
                Copy-Item -Path $_.FullName -Destination $targetDir -Recurse -Force
            } else {
                # For files, copy directly
                Copy-Item -Path $_.FullName -Destination $targetDir -Force
            }
        }
    }
}

# Copy documentation
$docsToBackup = @(
    "d:\sociorag\docs\phase4_final_completion_report.md",
    "d:\sociorag\docs\phase4_validation_summary.md",
    "d:\sociorag\docs\phase4_final_validation_summary.md",
    "d:\sociorag\docs\phase4_extended_implementation_summary.md"
)

$docsDir = Join-Path $backupDir "docs"
New-Item -Path $docsDir -ItemType Directory -Force | Out-Null

foreach ($doc in $docsToBackup) {
    if (Test-Path $doc) {
        $docName = Split-Path $doc -Leaf
        $docDestination = Join-Path $docsDir $docName
        Copy-Item -Path $doc -Destination $docDestination -Force
    }
}

Write-Host "Phase 4 files backed up to: $backupDir"

# Remove files after backup
Write-Host "Starting removal of backed up files..."

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        Write-Host "Removing file: $file"
        Remove-Item -Path $file -Force
    }
}

foreach ($dir in $backupDirs) {
    if (Test-Path $dir) {
        Write-Host "Removing directory: $dir"
        Remove-Item -Path $dir -Recurse -Force
    }
}

# Keep the documentation files
Write-Host "Documentation files are preserved in the docs directory."

Write-Host "Phase 4 cleanup script completed."
Write-Host "✅ Files have been backed up to: $backupDir"
Write-Host "✅ Temporary files have been removed."
Write-Host "✅ System is ready for Phase 5 development!"
