# Script to create a backup of Phase 6 files
# Created during Phase 6 housekeeping

# Get current timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "phase6_backup_$timestamp"

# Create backup directory
New-Item -Path "../$backupDir" -ItemType Directory -Force | Out-Null
New-Item -Path "../$backupDir/docs" -ItemType Directory -Force | Out-Null
New-Item -Path "../$backupDir/backend" -ItemType Directory -Force | Out-Null
New-Item -Path "../$backupDir/scripts" -ItemType Directory -Force | Out-Null

# Copy Phase 6 related documentation
Copy-Item -Path "../docs/phase6_*" -Destination "../$backupDir/docs/" -Recurse
Copy-Item -Path "../docs/api_*" -Destination "../$backupDir/docs/" -Recurse
Copy-Item -Path "../PHASE6_HOUSEKEEPING_REPORT.md" -Destination "../$backupDir/" -Recurse

# Copy API implementation files
Copy-Item -Path "../backend/app/api" -Destination "../$backupDir/backend/" -Recurse
Copy-Item -Path "../backend/app/main.py" -Destination "../$backupDir/backend/" -Recurse

# Copy test scripts
Copy-Item -Path "../scripts/test_phase6_api.py" -Destination "../$backupDir/scripts/" -Recurse

# Create README in backup directory
@"
# Phase 6 Backup - $timestamp

This directory contains a backup of key files from Phase 6 (API Integration & FastAPI Backend) of the SocioGraph project.

## Contents

- `/docs/` - Phase 6 documentation files
- `/backend/` - API implementation files
- `/scripts/` - Test scripts for API endpoints
- `PHASE6_HOUSEKEEPING_REPORT.md` - Housekeeping report for Phase 6

## Backup Date
$timestamp
"@ | Out-File -FilePath "../$backupDir/README.md"

Write-Host "Phase 6 backup created at $backupDir"
